import qrcode

# Generate QR code
def generate_qr_code():
    pdf_path = "output/line_card.pdf"
    shareable_link = "http://localhost:5000/output/line_card.pdf"

    qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
    )
    qr.add_data(shareable_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save("output/qrcode.png")
    print("QR code saved as 'qrcode.png'.")
