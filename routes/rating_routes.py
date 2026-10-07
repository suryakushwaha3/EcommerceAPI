from flask import request, jsonify

from operations.rating_operation import (
    create_rating,
    get_rating_by_id,
    get_product_rating,
    get_product_ratings,
    update_rating,
    delete_rating,
    update_rating_status
)


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def rating_routes(app):

    # =========================================================
    # CREATE RATING SUMMARY
    # POST /api/products/<product_id>/rating
    # =========================================================
    @app.route(
        "/api/products/<product_id>/rating",
        methods=["POST"]
    )
    def create_product_rating(product_id):

        data = request.get_json(silent=True) or {}

        result = create_rating(
            product_id=product_id,
            variant_id=data.get("variant_id"),

            five_star_count=_to_int(
                data.get("five_star_count"), 0
            ),

            four_star_count=_to_int(
                data.get("four_star_count"), 0
            ),

            three_star_count=_to_int(
                data.get("three_star_count"), 0
            ),

            two_star_count=_to_int(
                data.get("two_star_count"), 0
            ),

            one_star_count=_to_int(
                data.get("one_star_count"), 0
            ),

            verified_rating_count=_to_int(
                data.get("verified_rating_count"), 0
            ),

            unverified_rating_count=_to_int(
                data.get("unverified_rating_count"), 0
            ),

            last_rating_at=data.get("last_rating_at")
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 201


    # =========================================================
    # GET PRODUCT RATING
    # GET /api/products/<product_id>/rating
    #
    # Optional:
    # ?variant_id=VAR_xxxxx
    # =========================================================
    @app.route(
        "/api/products/<product_id>/rating",
        methods=["GET"]
    )
    def get_product_rating_route(product_id):

        variant_id = request.args.get("variant_id")

        result = get_product_rating(
            product_id=product_id,
            variant_id=variant_id
        )

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================================
    # GET ALL PRODUCT RATINGS
    # GET /api/products/<product_id>/ratings
    # =========================================================
    @app.route(
        "/api/products/<product_id>/ratings",
        methods=["GET"]
    )
    def get_product_ratings_route(product_id):

        result = get_product_ratings(product_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================================
    # GET RATING BY ID
    # GET /api/products/ratings/<rating_id>
    # =========================================================
    @app.route(
        "/api/products/ratings/<rating_id>",
        methods=["GET"]
    )
    def get_rating_by_id_route(rating_id):

        result = get_rating_by_id(rating_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================================
    # UPDATE RATING
    # PUT /api/products/ratings/<rating_id>
    # =========================================================
    @app.route(
        "/api/products/ratings/<rating_id>",
        methods=["PUT"]
    )
    def update_rating_route(rating_id):

        data = request.get_json(silent=True) or {}

        result = update_rating(
            rating_id=rating_id,

            five_star_count=(
                _to_int(data["five_star_count"])
                if "five_star_count" in data
                else None
            ),

            four_star_count=(
                _to_int(data["four_star_count"])
                if "four_star_count" in data
                else None
            ),

            three_star_count=(
                _to_int(data["three_star_count"])
                if "three_star_count" in data
                else None
            ),

            two_star_count=(
                _to_int(data["two_star_count"])
                if "two_star_count" in data
                else None
            ),

            one_star_count=(
                _to_int(data["one_star_count"])
                if "one_star_count" in data
                else None
            ),

            verified_rating_count=(
                _to_int(data["verified_rating_count"])
                if "verified_rating_count" in data
                else None
            ),

            unverified_rating_count=(
                _to_int(data["unverified_rating_count"])
                if "unverified_rating_count" in data
                else None
            ),

            last_rating_at=data.get("last_rating_at")
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200


    # =========================================================
    # DELETE RATING
    # DELETE /api/products/ratings/<rating_id>
    # =========================================================
    @app.route(
        "/api/products/ratings/<rating_id>",
        methods=["DELETE"]
    )
    def delete_rating_route(rating_id):

        result = delete_rating(rating_id)

        if not result["success"]:
            return jsonify(result), 404

        return jsonify(result), 200


    # =========================================================
    # UPDATE RATING STATUS
    # PUT /api/products/ratings/<rating_id>/status
    # =========================================================
    @app.route(
        "/api/products/ratings/<rating_id>/status",
        methods=["PUT"]
    )
    def update_rating_status_route(rating_id):

        data = request.get_json(silent=True) or {}

        status = data.get("status")

        result = update_rating_status(
            rating_id=rating_id,
            status=status
        )

        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200