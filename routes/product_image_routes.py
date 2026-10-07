from flask import jsonify, request

from operations.product_image_operation import (
    create_product_image,
    upload_product_image,
    get_product_image_by_id,
    get_product_images,
    update_product_image,
    delete_product_image,
    set_primary_product_image,
    set_thumbnail_product_image,
    update_product_image_status
)


def product_image_routes(app):

    # =====================================================
    # Create Product Image Using URL
    # =====================================================

    @app.route(
        "/api/products/<string:product_id>/images",
        methods=["POST"]
    )
    def create_product_image_route(product_id):

        data = request.get_json(
            silent=True
        ) or {}

        image_url = data.get(
            "image_url"
        )

        if not image_url:
            return jsonify({
                "success": False,
                "message": "Image URL is required."
            }), 400

        result = create_product_image(
            product_id=product_id,
            image_url=image_url,
            image_type=data.get(
                "image_type",
                "product"
            ),
            alt_text=data.get(
                "alt_text"
            ),
            title=data.get(
                "title"
            ),
            is_primary=data.get(
                "is_primary",
                0
            ),
            is_thumbnail=data.get(
                "is_thumbnail",
                0
            ),
            sort_order=data.get(
                "sort_order",
                0
            ),
            width=data.get(
                "width"
            ),
            height=data.get(
                "height"
            ),
            file_size=data.get(
                "file_size"
            ),
            mime_type=data.get(
                "mime_type"
            )
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 400

        return jsonify(result), 201


    # =====================================================
    # Upload Actual Product Image
    # =====================================================

    @app.route(
        "/api/products/<string:product_id>/images/upload",
        methods=["POST"]
    )
    def upload_product_image_route(product_id):

        image_file = request.files.get(
            "image"
        )

        if image_file is None:
            return jsonify({
                "success": False,
                "message": "Image file is required."
            }), 400

        try:
            sort_order = int(
                request.form.get(
                    "sort_order",
                    0
                )
            )
        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "message": "Sort order must be a number."
            }), 400

        is_primary = request.form.get(
            "is_primary",
            "0"
        ) in {
            "1",
            "true",
            "True",
            "yes",
            "on"
        }

        is_thumbnail = request.form.get(
            "is_thumbnail",
            "0"
        ) in {
            "1",
            "true",
            "True",
            "yes",
            "on"
        }

        result = upload_product_image(
            product_id=product_id,
            image_file=image_file,
            image_type=request.form.get(
                "image_type",
                "product"
            ),
            alt_text=request.form.get(
                "alt_text"
            ),
            title=request.form.get(
                "title"
            ),
            is_primary=is_primary,
            is_thumbnail=is_thumbnail,
            sort_order=sort_order
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 400

        return jsonify(result), 201


    # =====================================================
    # Get All Product Images
    # =====================================================

    @app.route(
        "/api/products/<string:product_id>/images",
        methods=["GET"]
    )
    def get_product_images_route(product_id):

        result = get_product_images(
            product_id
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 404

        return jsonify(result), 200


    # =====================================================
    # Get Product Image By ID
    # =====================================================

    @app.route(
        "/api/products/images/<string:image_id>",
        methods=["GET"]
    )
    def get_product_image_route(image_id):

        result = get_product_image_by_id(
            image_id
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 404

        return jsonify(result), 200


    # =====================================================
    # Update Product Image
    # =====================================================

    @app.route(
        "/api/products/images/<string:image_id>",
        methods=["PUT"]
    )
    def update_product_image_route(image_id):

        data = request.get_json(
            silent=True
        ) or {}

        result = update_product_image(
            image_id=image_id,
            **data
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 400

        return jsonify(result), 200


    # =====================================================
    # Delete Product Image
    # =====================================================

    @app.route(
        "/api/products/images/<string:image_id>",
        methods=["DELETE"]
    )
    def delete_product_image_route(image_id):

        result = delete_product_image(
            image_id
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 404

        return jsonify(result), 200


    # =====================================================
    # Set Primary Image
    # =====================================================

    @app.route(
        "/api/products/images/<string:image_id>/primary",
        methods=["PUT"]
    )
    def set_primary_product_image_route(
        image_id
    ):

        result = set_primary_product_image(
            image_id
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 404

        return jsonify(result), 200


    # =====================================================
    # Set Thumbnail Image
    # =====================================================

    @app.route(
        "/api/products/images/<string:image_id>/thumbnail",
        methods=["PUT"]
    )
    def set_thumbnail_product_image_route(
        image_id
    ):

        result = set_thumbnail_product_image(
            image_id
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 404

        return jsonify(result), 200


    # =====================================================
    # Update Image Status
    # =====================================================

    @app.route(
        "/api/products/images/<string:image_id>/status",
        methods=["PUT"]
    )
    def update_product_image_status_route(
        image_id
    ):

        data = request.get_json(
            silent=True
        ) or {}

        status = data.get(
            "status"
        )

        if not status:
            return jsonify({
                "success": False,
                "message": "Status is required."
            }), 400

        result = update_product_image_status(
            image_id=image_id,
            status=status
        )

        if not result.get(
            "success"
        ):
            return jsonify(result), 400

        return jsonify(result), 200