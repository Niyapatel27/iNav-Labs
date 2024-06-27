from flask import Flask,session,render_template,request,redirect,url_for,flash
import pyrebase
import firebase_admin
from firebase_admin import credentials,firestore
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import datetime
import uuid

load_dotenv()

app=Flask(__name__)
app.secret_key='secret'

config={
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

cred=credentials.Certificate("newkey.json")
firebase_admin.initialize_app(cred)
db=firestore.client()

configs={
    'apiKey': os.getenv("FIRE_API_KEY"),
    'authDomain': os.getenv("FIRE_AUTH_DOMAIN"),
    'projectId': os.getenv("FIRE_PROJECT_ID"),
    'storageBucket': os.getenv("FIRE_STORAGE_BUCKET"),
    'messagingSenderId': os.getenv("FIRE_MESSAGING_SENDER_ID"),
    'appId': os.getenv("FIRE_APP_ID"),
    'measurementId': os.getenv("FIRE_MEASUREMENT_ID"),
    'serviceAccount': os.getenv("FIRE_SERVICE_ACCOUNT"),
    'databaseURL': os.getenv("FIRE_DATABASE_URL")
}

firebases=pyrebase.initialize_app(configs)
storage=firebases.storage()

UPLOAD_FOLDER = '/tmp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        action = request.form.get('action')
        try:
            if action == "login":
                user = auth.sign_in_with_email_and_password(email, password)
                session['user'] = email
                session['role'] = role
                if role == 'owner':
                    return redirect(url_for('owner_home'))
                else:
                    return redirect(url_for('customer_home'))
            elif action == "signup":
                user = auth.create_user_with_email_and_password(email, password)
                session['user'] = email
                session['role'] = role
                if role == 'owner':
                    return redirect(url_for('owner_register'))
                else:
                    return redirect(url_for('customer_register'))
        except Exception as e:
            return f'Failed to login or sign up: {str(e)}'
    
    return render_template('index.html')

@app.route('/welcome',methods=['POST','GET'])
def welcome():
    if "user" in session:
        if request.method=='POST':
            name=request.form['name']
            email=request.form['email']
            mobile=request.form['mobile']
            canteen = request.form['canteen']
            chefs = request.form['chefs']
            upi = request.form['upi']
            doc_ref = db.collection('users').document()
            doc_ref.set({
            'name': name,
            'email': email,
            'mobile': mobile,
            'canteen':canteen,
            'chefs':chefs,
            'upi':upi
            })
            return render_template('upload_image.html')
        return render_template('owner_register.html')
    return redirect('/')

@app.route('/owner_home')
def owner_home():
    email = session['user']
    owner_id = get_owner_document_id(email)
    if not owner_id:
        return "Owner not found", 404

    owner_ref = db.collection('users').document(owner_id)
    menu_ref = owner_ref.collection('menu')
    items = menu_ref.stream()
    menu_items = [{'name': item.get('name'), 'price': item.get('price')} for item in items]

    orders_ref = owner_ref.collection('orders')
    orders = orders_ref.stream()
    order_items = []
    for order in orders:
        order_data = order.to_dict()
        customer = order_data.get('customer')
        order_id = order.id
        for item in order_data.get('items', []):
            order_items.append({
                'customer': customer,
                'item': item['item'],
                'price': item['price'],
                'order_id': order_id,
            })

    return render_template('owner_home.html', items=menu_items, orders=order_items)

@app.route('/review_order', methods=['POST'])
def review_order():
    order_id = request.form.get('order_id')
    item_name = request.form.get('item_name')
    action = request.form.get('action')

    email = session['user']
    owner_id = get_owner_document_id(email)
    if not owner_id:
        return "Owner not found", 404

    owner_ref = db.collection('users').document(owner_id)
    order_ref = owner_ref.collection('orders').document(order_id)
    order = order_ref.get()

    if order.exists:
        order_data = order.to_dict()
        items = order_data.get('items', [])
        for item in items:
            if item['item'] == item_name:
                # item['status'] = 'accepted' if action == 'accept' else 'rejected'
                if action=='accept':
                    item['status']='accepted'
                elif action=='cancel':
                    item['status']='cancelled'
                elif action=='ready':
                    item['status']='ready'
                elif action=='dispatch':
                    item['status']='dispatched'
                    #extra for canteen_order_history
                    history_canteen=owner_ref.collection('canteen_order_history').document(str(uuid.uuid4()))
                    customer_email=order_data.get('customer',[])
                    history_canteen.set({
                        'canteen email':email,
                        'item':item['item'],
                        'Date':datetime.datetime.now(),
                        'Customer email':customer_email,
                        'price':item['price']
                    })
                    #customer_order_history
                    customer_email=order_data.get('customer')
                    customer_order_ref=db.collection('customer_order_history').document(customer_email)
                    customer_order_doc=customer_order_ref.get()
                    order_details={
                        'canteen email':email,
                        'item':item['item'],
                        'price':item['price'],
                        'date':datetime.datetime.now()
                    }
                    if customer_order_doc.exists:
                        customer_order_data=customer_order_doc.to_dict()
                        if 'orders' in customer_order_data:
                            customer_order_data['orders'].append(order_details)
                        else:
                            customer_order_data['orders']=[order_details]
                        customer_order_ref.set(customer_order_data)
                    else:
                        customer_order_ref.set({
                            'customer_email':customer_email,
                            'orders':[order_details]
                        })
        order_ref.update({'items': items})
    flash(f'Item {action}ed successfully')
    return redirect(url_for('owner_home'))

@app.route('/customer_home',methods=['GET','POST'])
def customer_home():
    if 'user' in session and session['role'] == 'customer':
        docs=db.collection('users').get()
        canteen_names=[doc.to_dict().get('canteen') for doc in docs]
        if request.method=='POST':
            name=request.form.get('action')
            return redirect(url_for('open_specific',name=name))
        return render_template('customer_home.html',canteen_names=canteen_names)
    else:
        flash('Something is wrong...')
        return redirect(url_for('index'))

@app.route('/<name>',methods=['GET'])
def open_specific(name):
    user_choice=get_canteen(name)
    menu_ref=user_choice.reference.collection('menu')
    items=menu_ref.stream()
    menu_items=[{item.get('name'):item.get('price')} for item in items]
    return render_template('message.html',name=name,message=menu_items,choices=session.get(f'cart_{session["user"]}',[]))

@app.route('/add_to_cart',methods=['POST'])
def add_to_cart():
    item_names=request.form.getlist('food_item')
    canteen_name=request.form.get('canteen_name')
    user_cart_key=f'cart_{session["user"]}'
    if user_cart_key not in session:
        session[user_cart_key]=[]
    for item_name in item_names:
        item_price=request.form.get(f'food_price_{item_name}')
        session[user_cart_key].append({
            'canteen':canteen_name,
            'item':item_name,
            'price':item_price
        })
    flash(f"Added items to cart from {canteen_name}")
    return redirect(url_for('open_specific',name=canteen_name))

@app.route('/cart',methods=['GET'])
def cart():
    accepted_orders=[]
    cancelled_orders=[]
    pending_orders=[]
    cart_items=session.get(f'cart_{session["user"]}',[])
    total_price=sum(float(item['price']) for item in cart_items)
    return render_template('cart.html',cart=cart_items,total_price=total_price,accepted_orders=accepted_orders,pending_orders=pending_orders,cancelled_orders=cancelled_orders)

@app.route('/place_order',methods=['POST'])
def place_order():
    if 'user' not in session:
        flash('You need to log in to place an order.')
        return redirect(url_for('index'))
    user_id=session['user']
    cart_items=session.get(f'cart_{user_id}',[])
    if not cart_items:
        flash('Your cart is empty')
        return redirect(url_for('customer_home'))
    
    canteen_orders={}
    for item in cart_items:
        canteen_name=item['canteen']
        if canteen_name not in canteen_orders:
            canteen_orders[canteen_name]={
                'items':[],
                'canteen_name':canteen_name
            }
        canteen_orders[canteen_name]['items'].append({
            'item':item['item'],
            'price':item['price'],
            'status':'pending'
        })
    for canteen_name,order_data in canteen_orders.items():
        canteen_order_ref=db.collection('users').where('canteen','==',canteen_name).stream()
        for doc in canteen_order_ref:
            order_details={
                'customer':user_id,
                'items':[{'item': item['item'], 'price': item['price'], 'status': 'pending'} for item in order_data['items']],
                'timestamp':datetime.datetime.now()
            }
            doc.reference.collection('orders').add(order_details)

    # session[f'cart_{user_id}']=[]
    flash('Your order has been placed successfully')
    return redirect(url_for('cart'))

@app.route('/view_status',methods=['GET','POST'])
def view_status():
    accepted_orders=[]
    cancelled_orders=[]
    pending_orders=[]
    #extra
    ready_orders=[]
    dispatched_orders=[]
    #extra ended
    customer_email=session["user"]
    cart_items=session.get(f'cart_{customer_email}',[])
    total_price=sum(float(item['price']) for item in cart_items)
    users_ref=db.collection('users').stream()
    for user_doc in users_ref:
        orders_ref=db.collection('users').document(user_doc.id).collection('orders').where('customer','==',customer_email).get()
        for order_doc in orders_ref:
            order_data=order_doc.to_dict()
            for ordered_item in order_data.get('items',[]):
                if ordered_item.get('status')=='accepted':
                    accepted_orders.append(ordered_item['item'])
                elif ordered_item.get('status')=='cancelled':
                    cancelled_orders.append(ordered_item['item'])
                elif ordered_item.get('status')=='pending':
                    pending_orders.append(ordered_item['item'])
                #extra
                elif ordered_item.get('status')=='ready':
                    ready_orders.append(ordered_item['item'])
                elif ordered_item.get('status')=='dispatched':
                    dispatched_orders.append(ordered_item['item'])
                #extra ended
    return render_template('view_status.html',cart=cart_items,total_price=total_price,accepted_orders=accepted_orders,cancelled_orders=cancelled_orders,pending_orders=pending_orders,ready_orders=ready_orders,dispatched_orders=dispatched_orders)

@app.route('/owner_register')
def owner_register():
    if 'user' in session and session['role'] == 'owner':
        return render_template('owner_register.html')
    else:
        return redirect(url_for('index'))

@app.route('/customer_register')
def customer_register():
    if 'user' in session and session['role'] == 'customer':
        return render_template('customer_home.html')
    else:
        return redirect(url_for('index'))

#Functions
def get_owner_document_id(email):
    owners_ref = db.collection('users')
    query = owners_ref.where('email', '==', email).stream()
    for doc in query:
        return doc.id
    return None

def get_canteen(name):
    user_ref=db.collection('users').where('canteen','==',name).stream()
    user_choice=None
    for doc in user_ref:
        user_choice=doc
        break
    if not user_choice:
        return "Canteen not found",404
    return user_choice

@app.route('/add_item',methods=['POST'])
def add_item():
    return render_template('menu.html')

@app.route('/add',methods=['POST'])
def add():
    if request.method=='POST':
        item_name=request.form['item_name']
        item_price=request.form['item_price']
        email=session['user']
        owner_id=get_owner_document_id(email)
        if not owner_id:
            return "Owner not found",404
        owner_ref=db.collection('users').document(owner_id)
        menu_ref=owner_ref.collection('menu')
        menu_ref.add({'name':item_name,'price':item_price})
        return redirect(url_for('owner_home'))

@app.route('/upload',methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return "No file part"
    
    file=request.files['image']
    if file.filename=='':
        return "No selected file"
    
    if file:
        filename=secure_filename(file.filename)
        file_path=os.path.join(app.config['UPLOAD_FOLDER'],filename)
        file.save(file_path)

        #upload to filebase storage
        storage.child(f"images/{filename}").put(file_path)

        #clean up the saved file
        os.remove(file_path)
        return redirect(url_for('owner_home'))
    
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    session.pop('role', None)
    # session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=1111,debug=True)
