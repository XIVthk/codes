from app import app, db, User

with app.app_context():
    username = input("用户名: ")
    email = input("邮箱: ")
    password = input("密码: ")
    role = input("角色 (admin/moderator/user，默认 user): ") or 'user'
    
    if User.query.filter_by(username=username).first():
        print("❌ 用户名已存在")
    elif User.query.filter_by(email=email).first():
        print("❌ 邮箱已被注册")
    else:
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"✅ 用户 {username} 创建成功，角色: {role}")