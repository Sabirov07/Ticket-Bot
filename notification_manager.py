import smtplib

MY_EMAIL = "shakhzodbeksabirov@gmail.com"
MY_PASSWORD = "cbpxzzgdllxzorkr"


class NotificationManager:


    def send_email(self, city, price, email, user_name, link):
        message = f"Hello {user_name}!\n Flight to {city} is now {price}€\n More Details: {link}"

        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(MY_EMAIL, MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=email,
                msg=f"Subject:Price Alert from Extazy!\n\n{message}".encode("utf-8"))

        return "SUCCESS"