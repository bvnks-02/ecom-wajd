from flask import Flask, request, jsonify
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Cloudinary Configuration
cloudinary.config(
    cloud_name='dr0exmypg',
    api_key='644955431367616',
    api_secret='4LactM9w1Z31oIZ5VyPGF33cNA8'
)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# In-memory database (replace with real database in production)
products = []
product_id_counter = 1

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API 1: Add Product (from dashboard)
@app.route('/api/products', methods=['POST'])
def add_product():
    global product_id_counter
    
    try:
        # Check if image is in request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Image is required'
            }), 400
        
        image = request.files['image']
        
        # Check if file was selected
        if image.filename == '':
            return jsonify({
                'success': False,
                'message': 'No image selected'
            }), 400
        
        # Validate file type
        if not allowed_file(image.filename):
            return jsonify({
                'success': False,
                'message': 'Only image files (png, jpg, jpeg, gif, webp) are allowed'
            }), 400
        
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        prix = request.form.get('prix')
        
        # Validation
        if not name or not description or not prix:
            return jsonify({
                'success': False,
                'message': 'Name, description, and prix are required'
            }), 400
        
        # Upload image to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image,
            folder="ecommerce_products",
            resource_type="image",
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': 'auto'}
            ]
        )
        
        # Create product object
        product = {
            'id': product_id_counter,
            'name': name.strip(),
            'description': description.strip(),
            'prix': float(prix),
            'image': upload_result['secure_url'],
            'image_public_id': upload_result['public_id'],
            'createdAt': datetime.now().isoformat()
        }
        
        products.append(product)
        product_id_counter += 1
        
        return jsonify({
            'success': True,
            'message': 'Product added successfully',
            'product': product
        }), 201
        
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid price format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error adding product',
            'error': str(e)
        }), 500

# API 2: Get All Products (for homepage)
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        return jsonify({
            'success': True,
            'count': len(products),
            'products': products
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching products',
            'error': str(e)
        }), 500

# Get single product by ID
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        return jsonify({
            'success': True,
            'product': product
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error fetching product',
            'error': str(e)
        }), 500

# Delete product
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        # Delete image from Cloudinary
        if 'image_public_id' in product:
            cloudinary.uploader.destroy(product['image_public_id'])
        
        products.remove(product)
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error deleting product',
            'error': str(e)
        }), 500

# Update product
@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        # Update text fields
        if 'name' in request.form:
            product['name'] = request.form['name'].strip()
        if 'description' in request.form:
            product['description'] = request.form['description'].strip()
        if 'prix' in request.form:
            product['prix'] = float(request.form['prix'])
        
        # Update image if new one is uploaded
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '' and allowed_file(image.filename):
                # Delete old image from Cloudinary
                if 'image_public_id' in product:
                    cloudinary.uploader.destroy(product['image_public_id'])
                
                # Upload new image
                upload_result = cloudinary.uploader.upload(
                    image,
                    folder="ecommerce_products",
                    resource_type="image",
                    transformation=[
                        {'width': 800, 'height': 800, 'crop': 'limit'},
                        {'quality': 'auto'}
                    ]
                )
                
                product['image'] = upload_result['secure_url']
                product['image_public_id'] = upload_result['public_id']
        
        product['updatedAt'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'product': product
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid price format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error updating product',
            'error': str(e)
        }), 500

# Error handler for file size
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'message': 'File is too large. Maximum size is 5MB'
    }), 413

if __name__ == '__main__':
    print("Server is running on http://localhost:5000")
    print("Using Cloudinary for image storage")
    app.run(debug=True, port=5000)
