# Flask Warbler

Flask Warbler is a simple Twitter clone built with Flask, a popular Python web framework. It allows users to create accounts, post messages (called "warbles"), follow other users, and view a feed of warbles from the users they follow.

View the live demo [here](https://warbler-twitter-clone-by-d-lowes.onrender.com/)
**Sample login credentials**
**username:** tuckerdiane
**password:** password

## Features
- User registration and login: Users can create new accounts and log in with their credentials.
- Warble creation: Logged-in users can post new warbles.
- User profiles: Each user has a profile page displaying their warbles.
- Following system: Users can follow/unfollow other users to see their warbles in their own feed.
- Home feed: Users can view a feed of the latest warbles from the users they follow.
- Pagination: Warbles and user profiles are paginated to improve performance and navigation.

## Installation
To run Flask Warbler on your local machine, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/d-lowes/flask-warbler.git
```
2. Navigate to the project directory:

``` bash
cd flask-warbler
```

3. Create and activate a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # for Linux/Mac
venv\Scripts\activate  # for Windows
```

4. Install the required dependencies:

```bash
(venv) $ pip install -r requirements.txt
```

5. Set up the database:

```bash
(venv) $ psql
=# CREATE DATABASE warbler;
=# (control-d)
(venv) $ python seed.py
```
7. Create an .env file to hold configuration:

```.env
SECRET_KEY="whatever you desire"
DATABASE_URL=postgresql:///warbler
```


6. Start the Flask development server (sometimes default port 5000 is occupied for Mac users, depending on your machine):

```bash
(venv) $ flask run -p 5001
```

7. Open your web browser and navigate to http://localhost:5001 to access Flask Warbler.

## Configuration
Flask Warbler uses a configuration file to manage settings. By default, the development configuration is used. However, you can specify a different configuration by setting the FLASK_ENV environment variable. Available options are:

- development: Development configuration.
- production: Production configuration.
- testing: Testing configuration.
For example, to run Flask Warbler using the production configuration, set the environment variable before starting the server:

``` bash
export FLASK_ENV=production
flask run
```

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository. Please follow the existing code style and include tests with your contributions.
