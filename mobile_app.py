import os
import uuid
import json
import tempfile

import numpy as np
import streamlit as st

from pages.helper import db_queries
from pages.helper.data_models import PublicSubmissions
from pages.helper.match_algo import find_duplicate_cases
from pages.helper.face_embedding import embed_face
from pages.helper.utils import (
    image_obj_to_numpy,
    extract_face_mesh_landmarks,
    extract_unique_faces_from_video,
)

st.set_page_config("Public Submission", initial_sidebar_state="collapsed")
db_queries.create_db()


def _fmt(dt):
    return dt.strftime("%d %b %Y, %H:%M") if dt else "Not recorded"


def show_solved_case(case):
    """Render the original photo and details of an already solved case."""
    with st.container(border=True):
        photo_col, info_col = st.columns([1, 2])
        photo_path = f"./resources/{case['id']}.jpg"
        if os.path.exists(photo_path):
            photo_col.image(photo_path, caption="Original photo", width=180)
        else:
            photo_col.caption("Original photo not available")
        info_col.markdown(
            f"**{case['name']}**, age {case['age']}"
            f"{', ' + case['city'] if case['city'] else ''}\n\n"
            f"- Last seen: {case['last_seen']}\n"
            f"- Reported on: {_fmt(case['reported_on'])}\n"
            f"- Solved on: {_fmt(case['solved_on'])}\n"
            f"- Case ID: `{case['id']}`"
        )


def solved_matches(rgb_image, landmarks):
    """Solved cases showing the same person as the face in rgb_image."""
    pts = np.asarray(landmarks, dtype=float).reshape(-1, 3)
    h, w = rgb_image.shape[:2]
    near = (pts[:, 0].mean() * w, pts[:, 1].mean() * h)
    embedding = embed_face(rgb_image, near=near)
    return find_duplicate_cases(embedding, max_results=1, status="F")

st.title("Report a Sighting")

upload_mode = st.radio(
    "Upload type",
    options=["Image", "Video"],
    horizontal=True,
)

image_col, form_col = st.columns(2)
save_flag = 0
extracted_faces = []  # list of (landmarks, frame_rgb) for video mode
face_mesh = None  # single face for image mode
face_detected = False
unique_id = None
uploaded_file_path = None

# ── Image upload ──────────────────────────────────────────────────────────────
if upload_mode == "Image":
    with image_col:
        image_obj = st.file_uploader(
            "Upload photo", type=["jpg", "jpeg", "png"], key="user_submission_img"
        )
        if image_obj:
            unique_id = str(uuid.uuid4())

            with st.spinner("Processing..."):
                uploaded_file_path = "./resources/" + unique_id + ".jpg"
                with open(uploaded_file_path, "wb") as f:
                    f.write(image_obj.read())

                image_obj.seek(0)
                st.image(image_obj, width=200)
                image_obj.seek(0)
                image_numpy = image_obj_to_numpy(image_obj)
                face_mesh = extract_face_mesh_landmarks(image_numpy)

                if face_mesh is None:
                    if uploaded_file_path and os.path.exists(uploaded_file_path):
                        os.remove(uploaded_file_path)
                else:
                    face_detected = True
                    st.success("✅ Face detected.")

    solved = solved_matches(image_numpy, face_mesh) if face_detected else []
    if solved:
        if uploaded_file_path and os.path.exists(uploaded_file_path):
            os.remove(uploaded_file_path)
        st.warning(
            "✅ This person's case is already solved. No new submission is needed."
        )
        show_solved_case(solved[0])
    elif image_obj and face_detected:
        with form_col.form(key="image_submission_form"):
            sub_name = st.text_input("Your Name *")
            mobile_number = st.text_input("Your Mobile Number * (10 digits)")
            email = st.text_input("Your Email")
            address = st.text_input("Location where person was seen *")
            birth_marks = st.text_input("Birth Marks / Identifying Features")

            submit_bt = st.form_submit_button("Submit")

            if submit_bt:
                errors = []
                if not sub_name.strip():
                    errors.append("❌ Your Name is required.")
                if not mobile_number.strip():
                    errors.append("❌ Mobile Number is required.")
                elif (
                    not mobile_number.strip().isdigit()
                    or len(mobile_number.strip()) != 10
                ):
                    errors.append("❌ Mobile Number must be exactly 10 digits.")
                if not address.strip():
                    errors.append("❌ Location is required.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    details = PublicSubmissions(
                        submitted_by=sub_name.strip(),
                        location=address.strip(),
                        email=email.strip() or None,
                        face_mesh=json.dumps(face_mesh),
                        id=unique_id,
                        mobile=mobile_number.strip(),
                        birth_marks=birth_marks.strip() or None,
                        status="NF",
                    )
                    db_queries.new_public_case(details)
                    save_flag = 1

        if save_flag == 1:
            st.success("✅ Submission received. Thank you!")

# ── Video upload ──────────────────────────────────────────────────────────────
else:
    with image_col:
        video_obj = st.file_uploader(
            "Upload video", type=["mp4", "mov", "avi"], key="user_submission_video"
        )
        if video_obj:
            with st.spinner("Extracting faces from video..."):
                # Save to temp file so OpenCV can read it
                suffix = "." + video_obj.name.rsplit(".", 1)[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(video_obj.read())
                    tmp_path = tmp.name

                extracted_faces = extract_unique_faces_from_video(tmp_path)
                os.unlink(tmp_path)

                if not extracted_faces:
                    st.error(
                        "❌ No faces detected in the video.\n\n"
                        "**Tips:** ensure the video shows a clear front-facing view "
                        "of the person's face in good lighting."
                    )
                else:
                    st.success(f"✅ Found {len(extracted_faces)} unique face(s).")
                    st.caption("Detected faces:")
                    thumb_cols = st.columns(min(len(extracted_faces), 4))
                    for idx, (_, frame_rgb) in enumerate(extracted_faces):
                        thumb_cols[idx % 4].image(frame_rgb, width=100)

    new_faces = []
    for landmarks, frame in extracted_faces:
        solved = solved_matches(frame, landmarks)
        if solved:
            st.warning("✅ A person in this video already has a solved case.")
            show_solved_case(solved[0])
        else:
            new_faces.append((landmarks, frame))
    extracted_faces = new_faces

    if extracted_faces:
        with form_col.form(key="video_submission_form"):
            sub_name = st.text_input("Your Name *")
            mobile_number = st.text_input("Your Mobile Number * (10 digits)")
            email = st.text_input("Your Email")
            address = st.text_input("Location where person was seen *")
            birth_marks = st.text_input("Birth Marks / Identifying Features")

            submit_bt = st.form_submit_button(f"Submit {len(extracted_faces)} face(s)")

            if submit_bt:
                errors = []
                if not sub_name.strip():
                    errors.append("❌ Your Name is required.")
                if not mobile_number.strip():
                    errors.append("❌ Mobile Number is required.")
                elif (
                    not mobile_number.strip().isdigit()
                    or len(mobile_number.strip()) != 10
                ):
                    errors.append("❌ Mobile Number must be exactly 10 digits.")
                if not address.strip():
                    errors.append("❌ Location is required.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    count = 0
                    for landmarks, _ in extracted_faces:
                        sub_id = str(uuid.uuid4())
                        details = PublicSubmissions(
                            submitted_by=sub_name.strip(),
                            location=address.strip(),
                            email=email.strip() or None,
                            face_mesh=json.dumps(landmarks),
                            id=sub_id,
                            mobile=mobile_number.strip(),
                            birth_marks=birth_marks.strip() or None,
                            status="NF",
                        )
                        db_queries.new_public_case(details)
                        count += 1
                    st.success(f"✅ {count} submission(s) received. Thank you!")
