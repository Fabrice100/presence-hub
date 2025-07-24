from app import create_app, db

app = create_app()

with app.app_context():
    class TestTable(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(50))

    db.create_all()
    print("TestTable créée")