from app import app, db, User, ErrorEntry, ROLE_ADMIN

with app.app_context():
    # 删除所有表并重建
    db.drop_all()
    db.create_all()
    
    # 创建馆主账号
    admin = User(
        username='curator',
        email='curator@error.wiki',
        role=ROLE_ADMIN,
        bio='📚 错误档案馆创始人'
    )
    admin.set_password('admin123')  # 记得上线前改掉！
    db.session.add(admin)
    
    # 创建一个示例审核员
    moderator = User(
        username='mod',
        email='mod@error.wiki',
        role='moderator',
        bio='🔍 审核员'
    )
    moderator.set_password('mod123')
    db.session.add(moderator)
    
    db.session.commit()
    
    print("✅ 数据库已重建")
    print("📌 馆主账号: curator / admin123")
    print("📌 审核员账号: mod / mod123")