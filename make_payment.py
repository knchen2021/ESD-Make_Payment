from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests, os, sys, stripe

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('secret_key')
stripe.api_key = os.environ.get('stripeKey')

sendPayment_URL = "http://localhost:5000/payment"
updateStatusAppointment_URL = "http://localhost:5002/update_payment_status"

@app.route("/make_payment", methods=['POST'])
def make_payment():
    if request.is_json:
        try:
            # Get JSON Data
            paymentInfo = request.get_json()
            print("JSON Data:", paymentInfo)

            # Check if JSON Data has appointment_id
            if 'appointment_id' in paymentInfo:
                session['appointment_id'] = paymentInfo['appointment_id']
                print("Check if appointment_id is stored:", session.get('appointment_id'))
                
                # 1. Send the payment info
                # Invoke the payment microservice
                print('\n-----Invoking payment microservice-----')
                result = requests.post(sendPayment_URL, json=paymentInfo).json()
                print('payment_link:', result)
                return jsonify(result), result["code"]

        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line" + str(exc_tb.tb_lineno)
            print(ex_str)
        
    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

@app.route("/success")
def success():
    # Obtain Stripe checkout session information
    stripe_session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
    paymentStatus = stripe_session['payment_status']
    print("Payment Data from Stripe:", stripe_session)
    print("Payment Status:", paymentStatus)

    # Retrieve appointment_id
    appointment_id = session.get('appointment_id')
    print('Appointment ID from Session:', appointment_id)
    
    # Confirm if payment has been completed
    if paymentStatus == 'paid':
        # 2. Update Payment Status for appointment {payment_status}
        # Invoke the appointment microservice
        updateAppointment = {
            'appointment_id': appointment_id,
            'payment_status': True
        }

        print('\n-----Invoking appointment microservice-----') 
        paidStatus = requests.put(updateStatusAppointment_URL, json=updateAppointment).json()
        print('paid_status:', paidStatus)
        
        return jsonify(
            {
                "code": 200,
                "data": paidStatus['data'],
                "message": "Payment has been completed"
            }
        ), 200
    
    return jsonify(
        {
            "code": 404,
            "data": {
                "payment_status": paymentStatus
            },
            "message": "Payment not completed"
        }
    ), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)