from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from extractor import extract_text_from_image, extract_medicines_from_text
from scheduler import start_scheduler, stop_scheduler, schedule_medicines
import tempfile

# Lifespan handler to start/stop the scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🕒 Scheduler starting...")
    start_scheduler()  # Starts the scheduler loop
    yield
    print("🛑 Scheduler stopping...")
    stop_scheduler()  # Gracefully shuts down the scheduler

# Initialize FastAPI app with lifespan manager
app = FastAPI(lifespan=lifespan, title="EasyOCR + NLP Medicine Reminder API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "EasyOCR + NLP Medicine Reminder API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running successfully"}

@app.post("/upload/")
async def upload_prescription(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        print("🖼️ Upload received")

        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            image_path = tmp.name

        print(f"📂 Image saved to: {image_path}")

        # Extract text from image (OCR)
        extracted_text = extract_text_from_image(image_path)
        print("📄 Extracted Text:\n", extracted_text)

        # Parse medicine data from extracted text
        medicines = extract_medicines_from_text(extracted_text)
        print("💊 Extracted Medicines:\n", medicines)

        if not medicines:
            return JSONResponse({"error": "No medicines found"}, status_code=422)

        # Schedule medicine reminders (no instant sending)
        background_tasks.add_task(schedule_medicines, medicines)
        print("⏰ Scheduling reminders based on SLOTS")

        return {
            "message": "Reminders scheduled successfully!",
            "medicines": medicines
        }

    except Exception as e:
        print("❌ Exception:", str(e))
        return JSONResponse({"error": str(e)}, status_code=500)
