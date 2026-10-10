import json
import os
import uuid
from datetime import datetime, time

import streamlit as st

from pages.helper import db_queries
from pages.helper.data_models import PublicSubmissions
from pages.helper.face_embedding import embed_face
from pages.helper.match_algo import find_duplicate_cases
from pages.helper.utils import extract_face_mesh_landmarks, image_obj_to_numpy


def _fmt(dt):
    return dt.strftime("%d %b %Y") if dt else "Not recorded"


selected_case_id = st.session_state.get("selected_sighting_case_id")
selected_case = (
    db_queries.get_public_case_by_id(selected_case_id) if selected_case_id else None
)

st.markdown(
    '<div class="section-kicker">Make a difference</div><h1>Report a sighting</h1>',
    unsafe_allow_html=True,
)
if selected_case:
    (
        case_id,
        name,
        age,
        city,
        last_seen,
        birth_marks,
        description,
        reported_on,
        status,
    ) = selected_case
    photo_col, details_col = st.columns([1, 3])
    photo_path = f"./resources/{case_id}.jpg"
    if os.path.exists(photo_path):
        photo_col.image(photo_path, width=160)
    else:
        photo_col.caption("Photo unavailable")
    details_col.markdown(
        f"### Reporting a sighting of {name}\n"
        f"Age {age or '—'} · {city or 'Location not recorded'}  \n"
        f"Last seen: **{last_seen or 'Not recorded'}**  \n"
        f"Reported {_fmt(reported_on)}"
    )
    if birth_marks or description:
        details_col.caption(birth_marks or description)
    st.divider()
else:
    st.markdown(
        "Share what you saw and our officers will compare it with active cases. "
        "A photo helps our AI check solved cases, but it is completely optional."
    )

st.markdown("### Sighting details")

with st.form("sighting_form"):
    left, right = st.columns(2)
    with left:
        reporter_name = st.text_input("Your name *", placeholder="How can we contact you?")
        mobile = st.text_input("Mobile number *", placeholder="10 digits")
        email = st.text_input("Email (optional)")
        seen_date = st.date_input("When did you see them?", value=datetime.now().date())
        seen_time = st.time_input("Approximate time", value=time(12, 0))
    with right:
        location = st.text_input(
            "Where did you see them? *",
            placeholder="Area, landmark, city",
        )
        identifying_features = st.text_area(
            "Identifying features (optional)",
            placeholder="Clothing, belongings, birth marks, or anything memorable",
        )
        photo = st.file_uploader(
            "Photo (optional)",
            type=["jpg", "jpeg", "png"],
            help="A clear face photo lets us check whether the case is already solved.",
        )
    submitted = st.form_submit_button("Submit sighting", type="primary")

if not submitted:
    st.info("Please share the details above. Every useful detail can help.")
    st.stop()

errors = []
if not reporter_name.strip():
    errors.append("Your name is required.")
if not mobile.strip().isdigit() or len(mobile.strip()) != 10:
    errors.append("Mobile number must be exactly 10 digits.")
if not location.strip():
    errors.append("Location is required.")
if errors:
    for error in errors:
        st.error(error)
    st.stop()

if selected_case_id:
    current_case = db_queries.get_public_case_by_id(selected_case_id)
    if current_case is None:
        st.error("This case is no longer available. Please select another active case.")
        st.session_state.pop("selected_sighting_case_id", None)
        st.stop()
    if current_case[8] == "F":
        st.warning("Case already solved. Thank you for the effort.")
        st.session_state.pop("selected_sighting_case_id", None)
        st.stop()

face_mesh = None
match = []
photo_id = str(uuid.uuid4())
if photo:
    image_numpy = image_obj_to_numpy(photo)
    face_mesh = extract_face_mesh_landmarks(image_numpy)
    if face_mesh is None:
        st.error("We could not detect a face in that photo. You can submit without it.")
        st.stop()
    match = find_duplicate_cases(
        embed_face(image_numpy, near=(
            sum(point[0] for point in face_mesh) / len(face_mesh) * image_numpy.shape[1],
            sum(point[1] for point in face_mesh) / len(face_mesh) * image_numpy.shape[0],
        )),
        max_results=1,
        status="F",
    )

    if match:
        st.warning("Case already solved. Thank you for the effort.")
        solved_case = match[0]
        st.info(
            f"{solved_case['name']} was already marked as found. "
            "No new sighting was submitted."
        )
        st.stop()

observed_on = None
if seen_date:
    observed_on = datetime.combine(seen_date, seen_time).isoformat(timespec="minutes")

details = PublicSubmissions(
    submitted_by=reporter_name.strip(),
    location=location.strip(),
    email=email.strip() or None,
    face_mesh=json.dumps(face_mesh) if face_mesh is not None else "{}",
    id=photo_id,
    mobile=mobile.strip(),
    birth_marks=identifying_features.strip() or None,
    observed_on=observed_on,
    status="NF",
)
db_queries.new_public_case(details)
if photo:
    photo_path = f"./resources/{photo_id}.jpg"
    with open(photo_path, "wb") as file:
        file.write(photo.getvalue())
st.session_state.pop("selected_sighting_case_id", None)
st.success("Sighting received. Thank you for helping bring someone home.")
st.caption("Our officers will review the information and follow up if needed.")
