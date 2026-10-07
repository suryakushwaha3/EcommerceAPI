import os

from flask import (
    Flask,
    jsonify,
    send_from_directory
)

from flasgger import Swagger


# ============================================================
# Routes
# ============================================================

from routes.user_routes import user_routes
from routes.product_routes import product_routes
from routes.category_routes import category_routes
from routes.banner_routes import banner_routes
from routes.cart_routes import cart_routes
from routes.wishlist_routes import wishlist_routes
from routes.order_routes import order_routes
from routes.payment_routes import payment_routes
from routes.offer_routes import offer_routes
from routes.coupon_routes import coupon_routes
from routes.product_image_routes import product_image_routes
from routes.product_highlight_routes import product_highlight_routes
from routes.product_specification_routes import product_specification_routes
from routes.product_variant_routes import product_variant_routes
from routes.rating_routes import rating_routes
from routes.review_routes import review_routes


# ============================================================
# Swagger Tag Resolver
# ============================================================

def get_swagger_tag(route):
    """
    Generate Swagger tag from Flask API route.
    """

    parts = route.strip("/").split("/")

    if len(parts) < 2:
        return "Other"

    resource = parts[1]

    # --------------------------------------------------------
    # Product Related APIs
    # --------------------------------------------------------

    if resource == "products":

        if "images" in parts:
            return "Product Images"

        if "highlights" in parts:
            return "Product Highlights"

        if "specifications" in parts:
            return "Product Specifications"

        if "variants" in parts:
            return "Product Variants"

        return "Products"

    # --------------------------------------------------------
    # Other API Resources
    # --------------------------------------------------------

    tag_map = {
        "users": "Users",
        "categories": "Categories",
        "banners": "Banners",
        "cart": "Cart",
        "wishlist": "Wishlist",
        "orders": "Orders",
        "payments": "Payments",
        "reviews": "Reviews",
        "ratings": "Ratings",
        "offers": "Offers",
        "coupons": "Coupons"
    }

    return tag_map.get(
        resource,
        resource.replace("_", " ").title()
    )


# ============================================================
# Flask Route → Swagger Path
# ============================================================

def convert_flask_route_to_swagger(rule):
    """
    Convert Flask route parameters into Swagger parameters.

    Example:

    /api/products/<string:product_id>/images

    becomes:

    /api/products/{product_id}/images
    """

    route = rule.rule

    swagger_route = route

    path_parameters = []

    # --------------------------------------------------------
    # Flask Route Arguments
    # --------------------------------------------------------

    for argument in sorted(
        rule.arguments
    ):
        converter = None

        # Find converter from original route
        marker = f"<"

        start = route.find(
            marker,
            route.find(argument) - 20
            if route.find(argument) >= 0
            else 0
        )

        # ----------------------------------------------------
        # Detect exact Flask converter
        # ----------------------------------------------------

        if f"<string:{argument}>" in route:
            converter = "string"

        elif f"<int:{argument}>" in route:
            converter = "integer"

        elif f"<float:{argument}>" in route:
            converter = "number"

        elif f"<path:{argument}>" in route:
            converter = "string"

        elif f"<uuid:{argument}>" in route:
            converter = "string"

        elif f"<{argument}>" in route:
            converter = "string"

        # ----------------------------------------------------
        # Replace parameter
        # ----------------------------------------------------

        if converter:

            swagger_route = swagger_route.replace(
                f"<{converter}:{argument}>",
                f"{{{argument}}}"
            )

            swagger_route = swagger_route.replace(
                f"<{argument}>",
                f"{{{argument}}}"
            )

            parameter = {
                "name": argument,
                "in": "path",
                "required": True,
                "type": converter
            }

            if converter == "number":
                parameter["format"] = "float"

            path_parameters.append(
                parameter
            )

    return (
        swagger_route,
        path_parameters
    )


# ============================================================
# Swagger Request Body
# ============================================================

def create_request_body_parameter(
    method,
    route
):
    """
    Create a generic Swagger request body
    for POST / PUT / PATCH APIs.

    This allows Swagger UI to display
    a JSON request editor even when an
    endpoint does not have a manually
    defined schema.
    """

    if method.lower() not in {
        "post",
        "put",
        "patch"
    }:
        return None

    # --------------------------------------------------------
    # File Upload API
    # --------------------------------------------------------

    if route.endswith("/upload"):

        return {
            "name": "body",
            "in": "formData",
            "required": True,
            "type": "file",
            "description": "Upload file."
        }

    # --------------------------------------------------------
    # JSON Request Body
    # --------------------------------------------------------

    return {
        "name": "body",
        "in": "body",
        "required": False,
        "description": "JSON request body.",
        "schema": {
            "type": "object",
            "additionalProperties": True
        }
    }


# ============================================================
# Swagger Upload Parameters
# ============================================================

def create_upload_parameters(route):
    """
    Create Swagger parameters for multipart
    product image upload endpoints.
    """

    if not route.endswith("/upload"):
        return []

    return [
        {
            "name": "image",
            "in": "formData",
            "required": True,
            "type": "file",
            "description": "Product image file."
        },
        {
            "name": "image_type",
            "in": "formData",
            "required": False,
            "type": "string",
            "default": "product"
        },
        {
            "name": "alt_text",
            "in": "formData",
            "required": False,
            "type": "string"
        },
        {
            "name": "title",
            "in": "formData",
            "required": False,
            "type": "string"
        },
        {
            "name": "is_primary",
            "in": "formData",
            "required": False,
            "type": "boolean",
            "default": False
        },
        {
            "name": "is_thumbnail",
            "in": "formData",
            "required": False,
            "type": "boolean",
            "default": False
        },
        {
            "name": "sort_order",
            "in": "formData",
            "required": False,
            "type": "integer",
            "default": 0
        }
    ]


# ============================================================
# Swagger Paths Generator
# ============================================================

def generate_swagger_paths(app):
    """
    Automatically discover ALL Flask API routes
    and convert them into Swagger paths.
    """

    paths = {}

    # --------------------------------------------------------
    # Routes that should not appear
    # --------------------------------------------------------

    ignored_exact_routes = {
        "/",
        "/api/health",
        "/api/docs",
        "/swagger.json",
        "/oauth2-redirect.html",
        "/apidocs/index.html"
    }

    # --------------------------------------------------------
    # Loop through every registered Flask route
    # --------------------------------------------------------

    for rule in app.url_map.iter_rules():

        route = rule.rule

        # ----------------------------------------------------
        # Ignore non API routes
        # ----------------------------------------------------

        if route in ignored_exact_routes:
            continue

        if route.startswith("/static/"):
            continue

        if route.startswith("/flasgger_static/"):
            continue

        if not route.startswith("/api/"):
            continue

        # ----------------------------------------------------
        # Convert Flask path
        # ----------------------------------------------------

        (
            swagger_route,
            path_parameters
        ) = convert_flask_route_to_swagger(
            rule
        )

        # ----------------------------------------------------
        # Create Path
        # ----------------------------------------------------

        if swagger_route not in paths:
            paths[swagger_route] = {}

        # ----------------------------------------------------
        # HTTP Methods
        # ----------------------------------------------------

        methods = rule.methods - {
            "HEAD",
            "OPTIONS"
        }

        for method in sorted(methods):

            method = method.lower()

            tag = get_swagger_tag(
                route
            )

            # ------------------------------------------------
            # Operation
            # ------------------------------------------------

            operation = {
                "summary": (
                    rule.endpoint
                    .replace("_", " ")
                    .title()
                ),

                "description": (
                    f"API endpoint for "
                    f"`{method.upper()} {route}`."
                ),

                "operationId": (
                    f"{method}_{rule.endpoint}"
                ),

                "tags": [
                    tag
                ],

                "parameters": list(
                    path_parameters
                ),

                "responses": {
                    "200":{
                        "description":
                            "Request completed successfully."
                        }
                    },
                    "201": {
                        "description": (
                            "Resource created successfully."
                        )
                    },
                    "400": {
                        "description": (
                            "Bad request."
                        )
                    },
                    "404": {
                        "description": (
                            "Resource not found."
                        )
                    },
                    "405": {
                        "description": (
                            "Method not allowed."
                        )
                    },
                    "500": {
                        "description": (
                            "Internal server error."
                        )
                    }
                }
            

            # ------------------------------------------------
            # Upload API
            # ------------------------------------------------

            if route.endswith("/upload"):

                operation[
                    "consumes"
                ] = [
                    "multipart/form-data"
                ]

                operation[
                    "parameters"
                ].extend(
                    create_upload_parameters(
                        route
                    )
                )

            # ------------------------------------------------
            # JSON POST / PUT / PATCH
            # ------------------------------------------------

            else:

                body_parameter = (
                    create_request_body_parameter(
                        method,
                        route
                    )
                )

                if body_parameter:

                    operation[
                        "parameters"
                    ].append(
                        body_parameter
                    )

                    operation[
                        "consumes"
                    ] = [
                        "application/json"
                    ]

            # ------------------------------------------------
            # Add Operation
            # ------------------------------------------------

            paths[
                swagger_route
            ][method] = operation

    return paths


# ============================================================
# Swagger Template
# ============================================================

swagger_template = {

    "swagger": "2.0",

    "info": {

        "title": "Shopping API",

        "description": (
            "REST API for Shopping Application. "
            "Includes Users, Products, Categories, "
            "Banners, Cart, Wishlist, Orders, "
            "Payments, Reviews, Ratings, Offers, "
            "Coupons and Product Management."
        ),

        "version": "1.0.0"
    },

    "basePath": "/",

    "schemes": [
        "http",
        "https"
    ],

    "produces": [
        "application/json"
    ],

    # ========================================================
    # Swagger Tags
    # ========================================================

    "tags": [

        {
            "name": "Users",
            "description": (
                "User management and authentication."
            )
        },

        {
            "name": "Products",
            "description": (
                "Product management."
            )
        },

        {
            "name": "Product Images",
            "description": (
                "Product image management."
            )
        },

        {
            "name": "Product Highlights",
            "description": (
                "Product highlight management."
            )
        },

        {
            "name": "Product Specifications",
            "description": (
                "Product specification management."
            )
        },

        {
            "name": "Product Variants",
            "description": (
                "Product variant management."
            )
        },

        {
            "name": "Categories",
            "description": (
                "Category management."
            )
        },

        {
            "name": "Banners",
            "description": (
                "Banner management."
            )
        },

        {
            "name": "Cart",
            "description": (
                "Shopping cart management."
            )
        },

        {
            "name": "Wishlist",
            "description": (
                "Wishlist management."
            )
        },

        {
            "name": "Orders",
            "description": (
                "Order management."
            )
        },

        {
            "name": "Payments",
            "description": (
                "Payment and refund management."
            )
        },

        {
            "name": "Reviews",
            "description": (
                "Product review management."
            )
        },

        {
            "name": "Ratings",
            "description": (
                "Product rating management."
            )
        },

        {
            "name": "Offers",
            "description": (
                "Offer management."
            )
        },

        {
            "name": "Coupons",
            "description": (
                "Coupon management."
            )
        }
    ]
}


# ============================================================
# Swagger Config
# ============================================================

swagger_config = {

    "headers": [],

    "specs": [

        {
            "endpoint": "swagger",

            "route": "/swagger.json",

            "rule_filter": lambda rule: (
                rule.rule.startswith("/api/")
            ),

            "model_filter": lambda tag: True
        }
    ],

    "static_url_path": "/flasgger_static",

    "swagger_ui": True,

    "specs_route": "/api/docs"
}


# ============================================================
# Create Flask App
# ============================================================

def create_app():

    app = Flask(
        __name__
    )

    app.config[
        "JSON_SORT_KEYS"
    ] = False

    # ========================================================
    # Register All API Routes
    # ========================================================

    user_routes(app)

    product_routes(app)

    category_routes(app)

    banner_routes(app)

    cart_routes(app)

    wishlist_routes(app)

    order_routes(app)

    payment_routes(app)

    offer_routes(app)

    coupon_routes(app)

    product_image_routes(app)

    product_highlight_routes(app)

    product_specification_routes(app)

    product_variant_routes(app)

    rating_routes(app)

    review_routes(app)

    # ========================================================
    # Product Image Static Serving
    # ========================================================

    @app.route(
        "/uploads/products/<path:filename>",
        methods=["GET"]
    )
    def serve_product_image(filename):

        upload_folder = os.path.join(
            app.root_path,
            "uploads",
            "products"
        )

        return send_from_directory(
            upload_folder,
            filename
        )

    # ========================================================
    # Home
    # ========================================================

    @app.route(
        "/",
        methods=["GET"]
    )
    def home():

        return jsonify({

            "success": True,

            "message": (
                "Shopping API is running."
            ),

            "service": "ShoppingAPI",

            "version": "1.0.0"

        }), 200

    # ========================================================
    # Health Check
    # ========================================================

    @app.route(
        "/api/health",
        methods=["GET"]
    )
    def health_check():

        return jsonify({

            "success": True,

            "status": "healthy",

            "service": "ShoppingAPI"

        }), 200

    # ========================================================
    # 404
    # ========================================================

    @app.errorhandler(404)
    def not_found(error):

        return jsonify({

            "success": False,

            "message": (
                "API endpoint not found."
            )

        }), 404

    # ========================================================
    # 405
    # ========================================================

    @app.errorhandler(405)
    def method_not_allowed(error):

        return jsonify({

            "success": False,

            "message": (
                "HTTP method is not allowed "
                "for this endpoint."
            )

        }), 405

    # ========================================================
    # 500
    # ========================================================

    @app.errorhandler(500)
    def internal_server_error(error):

        return jsonify({

            "success": False,

            "message": (
                "Internal server error."
            )

        }), 500

    # ========================================================
    # Generate ALL Swagger Paths
    # ========================================================

    swagger_template[
        "paths"
    ] = generate_swagger_paths(
        app
    )

    # ========================================================
    # Initialize Flasgger
    # ========================================================

    Swagger(

        app,

        config=swagger_config,

        template=swagger_template

    )

    return app


# ============================================================
# Application Instance
# ============================================================

app = create_app()


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )