# quiz.py

from quiz import create_app

app = create_app()

if __name__ == "__main__":
    # Run the Flask dev server
    app.run(debug=True)
