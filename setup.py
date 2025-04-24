from setuptools import setup, find_packages

setup(
    name="prod",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "redis==5.0.1",
        "numpy==1.24.3",
        "opencv-python==4.8.1.78",
        "pydantic==2.5.2",
        "pydantic-settings==2.1.0",
        "python-dotenv==1.0.0",
        "ultralytics==8.3.111",
        "torch==2.1.0",
        "torchvision==0.16.0",
        "torchaudio==2.1.0",
        "prisma==0.11.0",
        "psycopg2-binary==2.9.9",
        "pgvector==0.2.3",
        "flask==2.2.3",
    ],
    description="Face Recognition System",
    author="YOLO CCTV Team",
    author_email="example@example.com",
) 