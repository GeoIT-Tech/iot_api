# from firebase import Firebase
# from firebase_admin import credentials,messaging

# cred = credentials.Certificate("ServiceKey.json")
# firebase_admin.initialize_app(cred)
# fcm = Firebase(config=firebase_config)

# def send_notification(title, msg,registration_token,dataObject=None):
#     message = messaging.MulticastMessage(
#         notification = messaging.Notification (
#             title = title,
#             body = msg
#         ),
#         data = dataObject,
#         tokens = registration_token
#     )
#     response = messaging.send_multicast(message)
#     print("Successfully sent notification",response)
#     return response