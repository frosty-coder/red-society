from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# File paths for JSON storage
USERS_FILE = 'data/users.json'
MESSAGES_FILE = 'data/messages.json'
FRIENDS_FILE = 'data/friends.json'
GROUPS_FILE = 'data/groups.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_messages():
    """Load messages from JSON file"""
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_messages(messages):
    """Save messages to JSON file"""
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=4)

def load_friends():
    """Load friends relationships from JSON file"""
    if os.path.exists(FRIENDS_FILE):
        with open(FRIENDS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_friends(friends):
    """Save friends relationships to JSON file"""
    with open(FRIENDS_FILE, 'w') as f:
        json.dump(friends, f, indent=4)

def load_groups():
    """Load groups from JSON file"""
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_groups(groups):
    """Save groups to JSON file"""
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f, indent=4)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("index.html", title="Red Society")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Please provide both username and password."

        users = load_users()
        if username in users:
            return "Username already exists. Please choose another one."

        users[username] = password
        save_users(users)
        
        # Initialize empty friends list
        friends = load_friends()
        friends[username] = []
        save_friends(friends)
        
        return render_template('pass.html', username=username)

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Please provide both username and password."

        users = load_users()
        if username in users:
            stored_password = users[username]
            if password == stored_password:
                session['username'] = username
                return render_template("index.html", title="Red Society")
        return render_template("wrongpass.html")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/save_message', methods=["POST"])
def save_message():
    try:
        if 'username' not in session:
            return jsonify({"error": "Not logged in"}), 401
            
        data = request.get_json()
        message_content = data.get("message", "")
        recipient = data.get("recipient", "")  # Can be username or group name
        is_group = data.get("isGroup", False)

        if not message_content:
            return jsonify({"error": "Message is empty"}), 400

        # Load existing messages
        messages = load_messages()

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_message = {
            "sender": session['username'],
            "content": message_content,
            "timestamp": timestamp
        }
        
        if is_group:
            new_message["group"] = recipient
        else:
            new_message["recipient"] = recipient

        messages.append(new_message)
        save_messages(messages)

        return jsonify({"status": "Message saved", "timestamp": timestamp}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_messages', methods=["GET"])
def get_messages():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    username = session['username']
    recipient = request.args.get("recipient", "")
    is_group = request.args.get("isGroup", "false").lower() == "true"
    
    messages = load_messages()
    filtered_messages = []
    
    if is_group:
        # Get group messages
        for message in messages:
            if message.get("group") == recipient:
                filtered_messages.append(message)
    else:
        # Get direct messages between two users
        for message in messages:
            if (message.get("sender") == username and message.get("recipient") == recipient) or \
               (message.get("sender") == recipient and message.get("recipient") == username):
                filtered_messages.append(message)
    
    return jsonify({"messages": filtered_messages})

@app.route('/get_all_users', methods=["GET"])
def get_all_users():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    users = load_users()
    return jsonify({"users": list(users.keys())})

@app.route('/search')
def search():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    query = request.args.get("name", "").strip().lower()

    if not query:
        return jsonify({"error": "No name provided"}), 400

    users = load_users()
    matching_names = [name for name in users.keys() if query in name.lower()]

    return jsonify({"matches": matching_names})

@app.route('/add_friend', methods=["POST"])
def add_friend():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    username = session['username']
    data = request.get_json()
    friend_name = data.get("friend", "")
    
    if not friend_name:
        return jsonify({"error": "No friend name provided"}), 400
        
    users = load_users()
    if friend_name not in users:
        return jsonify({"error": "User does not exist"}), 404
        
    if friend_name == username:
        return jsonify({"error": "Cannot add yourself as a friend"}), 400
        
    friends = load_friends()
    
    # Initialize if user doesn't have a friends list yet
    if username not in friends:
        friends[username] = []
        
    if friend_name in friends[username]:
        return jsonify({"error": "Already friends"}), 400
        
    # Add friend to user's friend list
    friends[username].append(friend_name)
    
    # Add user to friend's friend list (if not already there)
    if friend_name not in friends:
        friends[friend_name] = []
    if username not in friends[friend_name]:
        friends[friend_name].append(username)
        
    save_friends(friends)
    
    return jsonify({"status": "Friend added successfully"}), 200

@app.route('/get_friends', methods=["GET"])
def get_friends():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    username = session['username']
    friends = load_friends()
    
    if username not in friends:
        friends[username] = []
        save_friends(friends)
        
    return jsonify({"friends": friends[username]})

@app.route('/create_group', methods=["POST"])
def create_group():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    username = session['username']
    data = request.get_json()
    group_name = data.get("name", "")
    members = data.get("members", [])
    
    if not group_name:
        return jsonify({"error": "No group name provided"}), 400
        
    # Always add the creator to the group
    if username not in members:
        members.append(username)
        
    groups = load_groups()
    
    if group_name in groups:
        return jsonify({"error": "Group name already exists"}), 400
        
    groups[group_name] = {
        "creator": username,
        "members": members,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_groups(groups)
    
    return jsonify({"status": "Group created successfully"}), 200

@app.route('/get_groups', methods=["GET"])
def get_groups():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    username = session['username']
    groups = load_groups()
    
    # Find groups where the user is a member
    user_groups = {}
    for group_name, group_data in groups.items():
        if username in group_data.get("members", []):
            user_groups[group_name] = group_data
            
    return jsonify({"groups": user_groups})

if __name__ == '__main__':
    # Initialize empty JSON files if they don't exist
    if not os.path.exists(USERS_FILE):
        save_users({})
    if not os.path.exists(MESSAGES_FILE):
        save_messages([])
    if not os.path.exists(FRIENDS_FILE):
        save_friends({})
    if not os.path.exists(GROUPS_FILE):
        save_groups({})

    app.run(host='0.0.0.0', port=5000, debug=True)
