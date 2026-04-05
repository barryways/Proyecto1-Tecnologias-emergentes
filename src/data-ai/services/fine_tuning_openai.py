import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def init_fine_tuning():
    """
        Initializes fine-tuning process
        by uploading a dataset and creating a fine-tuning job.

        Training take 20 a 30 minutes.
        Watch in https://platform.openai.com/finetune
    """

    with open('dataset/dataset_openai.jsonl', 'rb') as f:
        response = openai_client.files.create(file=f, purpose='fine-tune')
    file_id = response.id

    job = openai_client.fine_tuning.jobs.create(
        training_file=file_id,
        model='gpt-3.5-turbo'
    )

    print(f'✅ File uploaded successfully. [ID] = {file_id}')
    print(f'✅ Job created successfully. [ID] = {job.id}')
    print(f"📊 Status: {job.status}")

def status_fine_tuning(job_id: str):
    """
    :param job_id:
    :return:
    """

    job = openai_client.fine_tuning.jobs.retrieve(job_id)
    print(f"📊 Status:          {job.status}")
    print(f"🤖 Model:           {job.fine_tuned_model}")
    print(f"📁 Base model:      {job.model}")
    print(f"📄 Training file:   {job.training_file}")
    print(f"🕐 Creado:          {job.created_at}")
    print(f"🕐 Finalizado:      {job.finished_at}")
    print(f"📈 Trained tokens:  {job.trained_tokens}")
    print(f"⚠️  Error:          {job.error}")

    events = openai_client.fine_tuning.jobs.list_events(
        fine_tuning_job_id=job_id,
        limit=10
    )
    for event in reversed(events.data):
        print(f"  {event.message}")
