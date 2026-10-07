from flask import request, jsonify

from operations.review_operation import (
    create_review,
    get_review_by_id,
    get_product_reviews,
    get_user_reviews,
    update_review,
    delete_review,
    moderate_review,
    mark_helpful,
    report_review,
    add_seller_response,
    feature_review,
    get_review_summary
)


# =========================================================
# HELPERS
# =========================================================

def _to_bool(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in (
            "true",
            "1",
            "yes",
            "on"
        )

    return default


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# REVIEW ROUTES
# =========================================================

def review_routes(app):

    # =====================================================
    # CREATE REVIEW
    # POST
    # /api/products/<product_id>/reviews
    # =====================================================

    @app.route(
        "/api/products/<product_id>/reviews",
        methods=["POST"]
    )
    def create_product_review(product_id):

        try:
            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "User ID is required"
                }), 400

            rating = _to_float(
                data.get("rating")
            )

            if rating is None:
                return jsonify({
                    "success": False,
                    "message": "Rating is required"
                }), 400

            result = create_review(
                user_id=user_id,
                product_id=product_id,
                rating=rating,
                review_title=data.get("review_title"),
                review_text=data.get("review_text"),
                variant_id=data.get("variant_id"),
                order_id=data.get("order_id"),
                order_item_id=data.get("order_item_id"),
                review_type=data.get(
                    "review_type",
                    "text"
                ),
                is_anonymous=_to_bool(
                    data.get("is_anonymous"),
                    False
                ),
                is_recommended=_to_bool(
                    data.get("is_recommended"),
                    True
                ),
                ip_address=request.remote_addr,
                user_agent=request.headers.get(
                    "User-Agent"
                )
            )

            return jsonify({
                "success": True,
                "message": "Review created successfully",
                "review": result
            }), 201

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to create review",
                "error": str(error)
            }), 500


    # =====================================================
    # GET REVIEW BY ID
    # GET
    # /api/reviews/<review_id>
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>",
        methods=["GET"]
    )
    def get_review(review_id):

        try:

            review = get_review_by_id(
                review_id
            )

            if not review:
                return jsonify({
                    "success": False,
                    "message": "Review not found"
                }), 404

            return jsonify({
                "success": True,
                "review": review
            }), 200

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to get review",
                "error": str(error)
            }), 500


    # =====================================================
    # GET PRODUCT REVIEWS
    #
    # GET
    # /api/products/<product_id>/reviews
    #
    # Query:
    # ?rating=5
    # ?verified_only=true
    # ?moderation_status=approved
    # ?limit=20
    # ?offset=0
    # =====================================================

    @app.route(
        "/api/products/<product_id>/reviews",
        methods=["GET"]
    )
    def product_reviews(product_id):

        try:

            rating = None

            rating_value = request.args.get(
                "rating"
            )

            if rating_value is not None:
                rating = _to_float(
                    rating_value
                )

                if rating is None:
                    return jsonify({
                        "success": False,
                        "message": "Invalid rating"
                    }), 400

            verified_only = _to_bool(
                request.args.get("verified_only"),
                False
            )

            moderation_status = request.args.get(
                "moderation_status",
                "approved"
            )

            limit = _to_int(
                request.args.get("limit"),
                20
            )

            offset = _to_int(
                request.args.get("offset"),
                0
            )

            if limit < 1:
                limit = 20

            if limit > 100:
                limit = 100

            if offset < 0:
                offset = 0

            reviews = get_product_reviews(
                product_id=product_id,
                rating=rating,
                verified_only=verified_only,
                moderation_status=moderation_status,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "product_id": product_id,
                "count": len(reviews),
                "limit": limit,
                "offset": offset,
                "reviews": reviews
            }), 200

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to get product reviews",
                "error": str(error)
            }), 500


    # =====================================================
    # GET USER REVIEWS
    #
    # GET
    # /api/users/<user_id>/reviews
    # =====================================================

    @app.route(
        "/api/users/<user_id>/reviews",
        methods=["GET"]
    )
    def user_reviews(user_id):

        try:

            limit = _to_int(
                request.args.get("limit"),
                20
            )

            offset = _to_int(
                request.args.get("offset"),
                0
            )

            if limit < 1:
                limit = 20

            if limit > 100:
                limit = 100

            if offset < 0:
                offset = 0

            reviews = get_user_reviews(
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            return jsonify({
                "success": True,
                "user_id": user_id,
                "count": len(reviews),
                "limit": limit,
                "offset": offset,
                "reviews": reviews
            }), 200

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to get user reviews",
                "error": str(error)
            }), 500


    # =====================================================
    # UPDATE REVIEW
    #
    # PUT
    # /api/reviews/<review_id>
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>",
        methods=["PUT"]
    )
    def update_review_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "User ID is required"
                }), 400

            rating = None

            if "rating" in data:
                rating = _to_float(
                    data.get("rating")
                )

            is_recommended = None

            if "is_recommended" in data:
                is_recommended = _to_bool(
                    data.get("is_recommended")
                )

            review = update_review(
                review_id=review_id,
                user_id=user_id,
                rating=rating,
                review_title=data.get(
                    "review_title"
                ),
                review_text=data.get(
                    "review_text"
                ),
                is_recommended=is_recommended
            )

            return jsonify({
                "success": True,
                "message": "Review updated successfully",
                "review": review
            }), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to update review",
                "error": str(error)
            }), 500


    # =====================================================
    # DELETE REVIEW
    #
    # DELETE
    # /api/reviews/<review_id>
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>",
        methods=["DELETE"]
    )
    def delete_review_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            user_id = data.get("user_id")

            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "User ID is required"
                }), 400

            result = delete_review(
                review_id=review_id,
                user_id=user_id
            )

            return jsonify(
                result
            ), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to delete review",
                "error": str(error)
            }), 500


    # =====================================================
    # MODERATE REVIEW
    #
    # PUT
    # /api/reviews/<review_id>/moderation
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>/moderation",
        methods=["PUT"]
    )
    def moderate_review_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            moderation_status = data.get(
                "moderation_status"
            )

            moderated_by = data.get(
                "moderated_by"
            )

            moderation_reason = data.get(
                "moderation_reason"
            )

            if not moderation_status:
                return jsonify({
                    "success": False,
                    "message": "Moderation status is required"
                }), 400

            if not moderated_by:
                return jsonify({
                    "success": False,
                    "message": "Moderated by is required"
                }), 400

            review = moderate_review(
                review_id=review_id,
                moderation_status=moderation_status,
                moderated_by=moderated_by,
                moderation_reason=moderation_reason
            )

            return jsonify({
                "success": True,
                "message": "Review moderation updated successfully",
                "review": review
            }), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to moderate review",
                "error": str(error)
            }), 500


    # =====================================================
    # HELPFUL / NOT HELPFUL
    #
    # POST
    # /api/reviews/<review_id>/helpful
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>/helpful",
        methods=["POST"]
    )
    def review_helpful_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            helpful = _to_bool(
                data.get("helpful"),
                True
            )

            review = mark_helpful(
                review_id=review_id,
                helpful=helpful
            )

            return jsonify({
                "success": True,
                "message": "Review helpfulness updated successfully",
                "review": review
            }), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to update helpfulness",
                "error": str(error)
            }), 500


    # =====================================================
    # REPORT REVIEW
    #
    # POST
    # /api/reviews/<review_id>/report
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>/report",
        methods=["POST"]
    )
    def report_review_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            reason = data.get(
                "reason"
            )

            review = report_review(
                review_id=review_id,
                reason=reason
            )

            return jsonify({
                "success": True,
                "message": "Review reported successfully",
                "review": review
            }), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to report review",
                "error": str(error)
            }), 500


    # =====================================================
    # SELLER RESPONSE
    #
    # PUT
    # /api/reviews/<review_id>/seller-response
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>/seller-response",
        methods=["PUT"]
    )
    def seller_response_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            seller_response = data.get(
                "seller_response"
            )

            seller_response_by = data.get(
                "seller_response_by"
            )

            if not seller_response:
                return jsonify({
                    "success": False,
                    "message": "Seller response is required"
                }), 400

            if not seller_response_by:
                return jsonify({
                    "success": False,
                    "message": "Seller response by is required"
                }), 400

            review = add_seller_response(
                review_id=review_id,
                seller_response=seller_response,
                seller_response_by=seller_response_by
            )

            return jsonify({
                "success": True,
                "message": "Seller response added successfully",
                "review": review
            }), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to add seller response",
                "error": str(error)
            }), 500


    # =====================================================
    # FEATURE / UNFEATURE REVIEW
    #
    # PUT
    # /api/reviews/<review_id>/featured
    # =====================================================

    @app.route(
        "/api/reviews/<review_id>/featured",
        methods=["PUT"]
    )
    def feature_review_route(review_id):

        try:

            data = request.get_json(silent=True) or {}

            is_featured = _to_bool(
                data.get("is_featured"),
                True
            )

            review = feature_review(
                review_id=review_id,
                is_featured=is_featured
            )

            return jsonify({
                "success": True,
                "message": "Review featured status updated successfully",
                "review": review
            }), 200

        except ValueError as error:

            return jsonify({
                "success": False,
                "message": str(error)
            }), 400

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to update featured status",
                "error": str(error)
            }), 500


    # =====================================================
    # REVIEW SUMMARY
    #
    # GET
    # /api/products/<product_id>/reviews/summary
    # =====================================================

    @app.route(
        "/api/products/<product_id>/reviews/summary",
        methods=["GET"]
    )
    def review_summary_route(product_id):

        try:

            summary = get_review_summary(
                product_id
            )

            return jsonify({
                "success": True,
                "product_id": product_id,
                "summary": summary
            }), 200

        except Exception as error:

            return jsonify({
                "success": False,
                "message": "Failed to get review summary",
                "error": str(error)
            }), 500