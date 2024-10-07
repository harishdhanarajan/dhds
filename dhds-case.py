import streamlit as st
from datetime import date
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader  # Import ImageReader to read images from BytesIO
from dateutil.relativedelta import relativedelta

def resize_and_crop(image_file, size):
    img = Image.open(image_file)
    # Resize the image to cover the target size while maintaining aspect ratio
    img.thumbnail((size * 2, size * 2))
    # Center crop to square
    width, height = img.size
    left = (width - size) / 2
    top = (height - size) / 2
    right = (width + size) / 2
    bottom = (height + size) / 2
    img = img.crop((left, top, right, bottom))
    return img

def display_square_images(upload_key, caption):
    uploaded_files = st.file_uploader(caption, type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    images = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            image = resize_and_crop(uploaded_file, 300)  # 300px square
            st.image(image, caption=uploaded_file.name, use_column_width=True)
            images.append(uploaded_file)
    return images

# Custom CSS for better alignment
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: 1000px;
        padding-top: 5rem;
        padding-bottom: 5rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stTextArea > div > div > textarea {
        font-size: 16px;
    }
    .stSelectbox > div > div > select {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.title("Case History Form")
st.write("Dr. Hema's Dental Studio - Kids | Family Dentistry")

st.header("Patient Information")
name = st.text_input("Full Name *")
col1, col2 = st.columns(2)
with col1:
    # Set date range for date of birth picker
    today = date.today()

    # Calculate the date 75 years ago from today
    def get_date_years_ago(d, years):
        try:
            return d.replace(year=d.year - years)
        except ValueError:
            # Handle leap years
            return d.replace(month=2, day=28, year=d.year - years)

    min_date = get_date_years_ago(today, 75)
    dob = st.date_input("Date of Birth *", value=today, min_value=min_date, max_value=today)

    # Calculate age in years, months, and days
    def calculate_age(born):
        delta = relativedelta(today, born)
        return delta.years, delta.months, delta.days

    years, months, days = calculate_age(dob)
    st.write(f"Age: {years}Y {months:02d}M {days:02d}D")
with col2:
    gender = st.selectbox("Gender *", ("Male", "Female", "Other"))

st.header("Medical Information")
chiefcomplaint = st.text_area("Chief Complaint *", height=150)
historyofpresentingillness = st.text_area("History of Presenting Illness *", height=150)
pastmedicalhistory = st.text_area("Past Medical History *", height=150)
pastdentalhistory = st.text_area("Past Dental History *", height=150)
habithistory = st.text_area("Family History *", height=150)
drughistory = st.text_area("Drug History *", height=150)

st.header("Clinical Findings")
intraoral = st.text_area("Intraoral Findings *")
intraoral_pics = display_square_images("Intraoral Pictures *", "Upload Intraoral Pictures")

extraoral = st.text_area("Extra Oral Findings *")
extraoral_pics = display_square_images("Extra Oral Pictures *", "Upload Extra Oral Pictures")

st.header("Radiographic Findings")
radiographic_findings = st.text_area("Radiographic Findings *", height=150)
radiographic_pics = display_square_images("Radiographic Pictures *", "Upload Radiographic Pictures")

st.header("Treatment Plan")
treatment_plan = st.text_area("Treatment Plan *", height=150)

st.header("Treatment Done and Medication Prescribed")
treatment_done = st.text_area("Treatment Done *", height=150)
post_op_pics = display_square_images("Post Operative Pictures *", "Upload Post Operative Pictures")

def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph("Case History Form", styles['Title']))
    story.append(Spacer(1, 12))

    # Add form data
    for key, value in data.items():
        if key.endswith('Pictures') and value:
            # Handle multiple images
            story.append(Paragraph(key, styles['Heading2']))
            for idx, img_file in enumerate(value):
                # Read image from UploadedFile
                img = Image.open(img_file)
                # Resize image for PDF
                img_width = 200  # Adjusted width
                img_height = img.height * (img_width / img.width)  # Maintain aspect ratio
                # Convert image to BytesIO
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                # Use ImageReader to read image from BytesIO
                rl_image = RLImage(ImageReader(img_byte_arr), width=img_width, height=img_height)
                story.append(rl_image)
                story.append(Spacer(1, 12))
        elif key.endswith('Picture') and value:
            # Handle single image (if any)
            img = Image.open(value)
            story.append(Paragraph(key, styles['Heading2']))
            # Resize image for PDF
            img_width = 200  # Adjusted width
            img_height = img.height * (img_width / img.width)  # Maintain aspect ratio
            # Convert image to BytesIO
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            # Use ImageReader to read image from BytesIO
            rl_image = RLImage(ImageReader(img_byte_arr), width=img_width, height=img_height)
            story.append(rl_image)
            story.append(Spacer(1, 12))
        elif isinstance(value, (str, int, float, date)):
            # Add text data
            story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
            story.append(Spacer(1, 12))
        else:
            # Skip non-text data
            continue

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

if st.button("Submit"):
    # Check if all mandatory fields are filled
    mandatory_fields = [name, gender, chiefcomplaint, historyofpresentingillness, 
                        pastmedicalhistory, pastdentalhistory, habithistory, 
                        drughistory, intraoral, extraoral, radiographic_findings, 
                        treatment_plan, treatment_done]
    
    if all(mandatory_fields):
        # Create a dictionary with all form data
        form_data = {
            "Full Name": name,
            "Date of Birth": dob,
            "Age": f"{years}Y {months:02d}M {days:02d}D",
            "Gender": gender,
            "Chief Complaint": chiefcomplaint,
            "History of Presenting Illness": historyofpresentingillness,
            "Past Medical History": pastmedicalhistory,
            "Past Dental History": pastdentalhistory,
            "Family History": habithistory,
            "Drug History": drughistory,
            "Intraoral Findings": intraoral,
            "Intraoral Pictures": intraoral_pics,
            "Extra Oral Findings": extraoral,
            "Extra Oral Pictures": extraoral_pics,
            "Radiographic Findings": radiographic_findings,
            "Radiographic Pictures": radiographic_pics,
            "Treatment Plan": treatment_plan,
            "Treatment Done": treatment_done,
            "Post Operative Pictures": post_op_pics
        }
        
        # Generate PDF
        pdf_data = create_pdf(form_data)
        
        # Provide download link for the PDF
        st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name=f"case_history_{name}.pdf",
            mime="application/pdf"
        )
        
        st.success("Thank you for submitting the form. You can now download the PDF.")
    else:
        st.error("Please fill in all mandatory fields and upload all required images.")
