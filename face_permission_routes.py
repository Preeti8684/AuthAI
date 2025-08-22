def permission_verify():
    """Verify user permission from email link."""
    token = request.args.get("token")
    granted = request.args.get("granted", "false").lower() == "true"
    
    if not token:
        return render_template("permission_invalid.html", error="Missing token")
    
    try:
        # Find user with this token
        user = db.users.find_one({
            "permission_token": token,
            "permission_token_expiry": {"$gt": datetime.utcnow()}
        })
        
        if not user:
            return render_template("permission_invalid.html", error="Invalid or expired token. For security reasons, permission links expire after 30 minutes.")
        
        # Update user's permission status
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "permission_granted": granted,
                "permission_date": datetime.utcnow()
            },
            "$unset": {
                "permission_token": "",
                "permission_token_expiry": ""
            }}
        )
    except Exception as e:
        return render_template("permission_invalid.html", error=str(e)) 