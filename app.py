from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from models import db, User , Idea , Vote, Comment
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///innovation_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my_secret_key'  


db.init_app(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            
            login_user(user)
            
            flash('Login successful!', 'success')
            
           
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    
    ideas = Idea.query.all()
    return render_template('dashboard.html', ideas=ideas)

@app.route('/submit_idea', methods=['GET', 'POST'])
@login_required
def submit_idea():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        new_category = request.form.get('new_category')  

        
        if new_category.strip():  
            category = new_category.strip()
        elif not category:  
            flash("Please select or enter a category.", 'danger')
            return redirect(url_for('submit_idea'))

        
        new_idea = Idea(title=title, description=description, category=category, submitter_id=current_user.id)

        
        db.session.add(new_idea)
        db.session.commit()

        flash("Idea submitted successfully!", 'success')
        return redirect(url_for('dashboard'))

    
    categories = ['Technology', 'Process Improvement', 'Customer Experience']
    return render_template('submit_idea.html', categories=categories)


@app.route('/idea/<int:idea_id>')
def view_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    
    
    upvotes = Vote.query.filter_by(idea_id=idea.id, vote_type='upvote').count()
    downvotes = Vote.query.filter_by(idea_id=idea.id, vote_type='downvote').count()

    
    comments = db.session.query(Comment, User.username).join(User).filter(
        Comment.idea_id == idea_id, 
        Comment.parent_id == None
    ).order_by(Comment.timestamp.desc()).all()

    
    for i, (comment, username) in enumerate(comments):
        replies = db.session.query(Comment, User.username).join(User).filter(
            Comment.parent_id == comment.id
        ).order_by(Comment.timestamp.desc()).all()
        
        
        comments[i] = (comment, username, replies)
    
    return render_template(
        'view_idea.html', 
        idea=idea, 
        upvotes=upvotes, 
        downvotes=downvotes, 
        comments=comments
    )



@app.route('/vote/<int:idea_id>/<vote_type>', methods=['POST'])
@login_required
def vote(idea_id, vote_type):
    if vote_type not in ['upvote', 'downvote']:
        flash("Invalid vote type", 'danger')
        return redirect(url_for('dashboard'))

    
    existing_vote = Vote.query.filter_by(idea_id=idea_id, user_id=current_user.id).first()

    if existing_vote:
       
        existing_vote.vote_type = vote_type
        db.session.commit()
        flash(f"Your vote for this idea has been updated to {vote_type}.", 'success')
    else:
       
        new_vote = Vote(idea_id=idea_id, user_id=current_user.id, vote_type=vote_type)
        db.session.add(new_vote)
        db.session.commit()
        flash(f"Your {vote_type} has been recorded.", 'success')

    return redirect(url_for('view_idea', idea_id=idea_id)) 

@app.route('/idea/<int:idea_id>/add_comment', methods=['POST'])
def add_comment(idea_id):
    content = request.form.get('content')
    parent_id = request.form.get('parent_id') 

    if not content.strip():
        flash('Comment content cannot be empty.', 'error')
        return redirect(url_for('view_idea', idea_id=idea_id))

    user_id = current_user.id 

   
    new_comment = Comment(
        idea_id=idea_id,
        user_id=user_id,
        content=content,
        parent_id=parent_id if parent_id else None 
    )

    db.session.add(new_comment)
    db.session.commit()

    flash('Comment added successfully!', 'success')
    return redirect(url_for('view_idea', idea_id=idea_id))

if __name__ == "__main__":
    app.run(debug=True)

