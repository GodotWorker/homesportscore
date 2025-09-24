from flask import Flask

# Create an instance of the Flask class
app = Flask(__name__)

# Define a route for the root URL ("/")
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# Run the application if the script is executed directly
if __name__ == "__main__":
    app.run(debug=True) # debug=True enables debugging features
