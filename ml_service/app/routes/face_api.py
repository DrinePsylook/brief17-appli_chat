# ml_service/app/routes/face_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import face_recognition
import cv2
import numpy as np

from ..database import get_db, FaceEncoding
from ..models.face_models import VerificationResponse, IdentificationResponse, StandardResponse

router = APIRouter(prefix="/face", tags=["face_recognition"])

@router.post("/register/{user_id}", response_model=StandardResponse, status_code=201)
async def register_face_route(user_id: str, image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        image_bytes = await image.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image_rgb = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(image_rgb)
        if not face_locations:
            raise HTTPException(status_code=400, detail="Aucun visage détecté.")
        
        face_encoding = face_recognition.face_encodings(image_rgb, face_locations)[0]

        db_encoding = FaceEncoding(user_id=user_id, encoding=face_encoding.tolist())
        # Utilisation de merge pour insérer ou mettre à jour (upsert)
        db.merge(db_encoding)
        db.commit()
        
        return {"status": "success", "message": "Visage enregistré avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")

@router.post("/verify/{user_id}", response_model=VerificationResponse)
async def verify_face_route(user_id: str, image: UploadFile = File(...), db: Session = Depends(get_db)):
    db_encoding = db.query(FaceEncoding).filter(FaceEncoding.user_id == user_id).first()
    if not db_encoding:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    try:
        image_bytes = await image.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image_rgb = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        
        face_locations = face_recognition.face_locations(image_rgb)
        if not face_locations:
            return {"status": "failure", "match": False, "message": "Aucun visage détecté."}

        unknown_encoding = face_recognition.face_encodings(image_rgb, face_locations)[0]
        known_encoding = np.array(db_encoding.encoding)

        # La ligne de comparaison est un peu longue, donc on la met sur plusieurs lignes pour la lisibilité
        match = face_recognition.compare_faces(
            [known_encoding],
            unknown_encoding
        )[0]
        
        return {"status": "success", "match": match, "message": "Vérification réussie." if match else "Vérification échouée."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")

@router.post("/identify", response_model=IdentificationResponse)
async def identify_face_route(image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        image_bytes = await image.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        image_rgb = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(image_rgb)
        if not face_locations:
            return {"status": "failure", "user_id": None, "confidence": None, "message": "Aucun visage détecté."}
        
        unknown_encoding = face_recognition.face_encodings(image_rgb, face_locations)[0]
        
        known_encodings_db = db.query(FaceEncoding).all()
        known_encodings = [np.array(e.encoding) for e in known_encodings_db]
        known_ids = [e.user_id for e in known_encodings_db]
        
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding)
        
        user_id = None
        confidence = None
        if True in matches:
            first_match_index = matches.index(True)
            user_id = known_ids[first_match_index]
            face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)
            confidence = 1 - face_distances[first_match_index]
        
        return {"status": "success", "user_id": user_id, "confidence": confidence, "message": "Identification réussie." if user_id else "Visage non identifié."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")