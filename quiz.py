# app.py
# Ear Health Quiz for Streamlit Cloud
# - Student enters Student ID every time
# - Can play only today's 2 questions
# - Saves real student_id to GitHub CSV
# - Shows user's accumulated score
# - Shows current highest accumulated score without showing Student ID
# - Supports multiple correct answers for selected questions via "answers"

import streamlit as st
import pandas as pd
import requests
import base64
import json
from datetime import datetime, date
from zoneinfo import ZoneInfo
from io import StringIO

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Ear Health Quiz",
    page_icon="👂",
    layout="centered"
)

BKK = ZoneInfo("Asia/Bangkok")

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
OWNER = st.secrets["GITHUB_OWNER"]
REPO = st.secrets["GITHUB_REPO"]
BRANCH = st.secrets.get("GITHUB_BRANCH", "main")
CSV_PATH = st.secrets.get("SCORE_CSV_PATH", "ear_quiz_scores.csv")
START_DATE = date.fromisoformat(st.secrets.get("START_DATE", "2026-06-18"))

# =========================
# QUESTIONS: 120 questions
# difficulty: easy=1, medium=2, hard=3
# =========================

QUESTIONS = [
    # =====================
    # A. Ear health knowledge 60 questions
    # =====================
    {
        "q": "ขี้หูมีประโยชน์หลักคืออะไร?",
        "choices": ["ทำให้หูมีกลิ่น", "ป้องกันฝุ่นและเชื้อโรค", "ทำให้เสียงดังขึ้น", "ทำให้หูเปียก"],
        "answer": "ป้องกันฝุ่นและเชื้อโรค",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "ผลที่พบบ่อยจากการใช้คอตตอนบัดแคะหูลึก ๆ คืออะไร?",
        "choices": ["ขี้หูถูกดันลึกเข้าไป", "ทำให้หูสะอาดถาวร", "ทำให้ได้ยินดีขึ้นเสมอ", "ไม่มีผลเสีย"],
        "answer": "ขี้หูถูกดันลึกเข้าไป",
        "answers": ["ขี้หูถูกดันลึกเข้าไป"],
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "อาการหูอื้อเฉียบพลันข้างเดียวควรทำอย่างไร?",
        "choices": ["รอดู 1 เดือน", "รีบพบแพทย์", "แคะหูแรง ๆ", "ซื้อยาหยอดเอง"],
        "answer": "รีบพบแพทย์",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "เสียงดังทำลายส่วนใดในหูชั้นใน?",
        "choices": ["เซลล์ขนในคอเคลีย", "ใบหู", "ติ่งหู", "ท่อยูสเตเชียน"],
        "answer": "เซลล์ขนในคอเคลีย",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "เซลล์ขนรับเสียงในหูชั้นในเมื่อถูกทำลายแล้วมักเป็นอย่างไร?",
        "choices": ["งอกใหม่ได้ง่าย", "มักฟื้นกลับเต็มที่", "มักฟื้นกลับไม่ได้", "ไม่มีผลต่อการได้ยิน"],
        "answer": "มักฟื้นกลับไม่ได้",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "หลัก 60/60 สำหรับการใช้หูฟังคืออะไร?",
        "choices": ["ไม่เกิน 60% ของความดัง ไม่เกิน 60 นาทีต่อครั้ง", "ฟัง 60 เพลง", "ใช้หูฟัง 60 บาท", "ฟังได้ 60 ชั่วโมง"],
        "answer": "ไม่เกิน 60% ของความดัง ไม่เกิน 60 นาทีต่อครั้ง",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "อาการใดเป็นสัญญาณเตือนควรตรวจหู?",
        "choices": ["หูอื้อเรื้อรัง", "มีน้ำหรือหนองไหลจากหู", "ปวดหูมาก", "ถูกทุกข้อ"],
        "answer": "ถูกทุกข้อ",
        "answers": ["หูอื้อเรื้อรัง", "มีน้ำหรือหนองไหลจากหู", "ปวดหูมาก", "ถูกทุกข้อ"],
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "หูชั้นกลางเชื่อมกับคอผ่านท่อใด?",
        "choices": ["ท่อยูสเตเชียน", "หลอดลม", "หลอดอาหาร", "ท่อน้ำตา"],
        "answer": "ท่อยูสเตเชียน",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "หูอื้อเวลาเครื่องบินขึ้นลงเกี่ยวข้องกับอะไร?",
        "choices": ["ความดันอากาศเปลี่ยน", "น้ำตาลต่ำ", "สายตาสั้น", "ไตทำงานหนัก"],
        "answer": "ความดันอากาศเปลี่ยน",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "วิธีช่วยลดหูอื้อบนเครื่องบินคือข้อใด?",
        "choices": ["กลืน น้ำลาย หาว หรือเคี้ยวหมากฝรั่ง", "แคะหู", "กลั้นหายใจนาน ๆ", "ตะโกน"],
        "answer": "กลืน น้ำลาย หาว หรือเคี้ยวหมากฝรั่ง",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "หากมีเลือดออกจากหูหลังอุบัติเหตุควรทำอย่างไร?",
        "choices": ["รีบพบแพทย์", "หยอดแอลกอฮอล์", "ใช้สำลีดันลึก", "นอนรอดู"],
        "answer": "รีบพบแพทย์",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "อาการบ้านหมุนอาจเกี่ยวข้องกับส่วนใด?",
        "choices": ["หูชั้นใน", "เล็บ", "กระเพาะ", "ผิวหนัง"],
        "answer": "หูชั้นใน",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "การใช้หูฟังร่วมกับผู้อื่นเสี่ยงต่ออะไร?",
        "choices": ["ติดเชื้อที่หู", "สายตาดีขึ้น", "เสียงเบาลง", "ผมร่วง"],
        "answer": "ติดเชื้อที่หู",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "ควรทำความสะอาดหูฟังเป็นระยะเพื่ออะไร?",
        "choices": ["ลดเชื้อโรคและคราบสกปรก", "เพิ่มแบตเตอรี่", "ทำให้เพลงเพราะขึ้นเสมอ", "ลดน้ำหนัก"],
        "answer": "ลดเชื้อโรคและคราบสกปรก",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "น้ำเข้าหูหลังว่ายน้ำควรทำอย่างไร?",
        "choices": ["เอียงศีรษะให้น้ำไหลออก", "ใช้ของแข็งแหย่", "ใช้ปากกาเขี่ย", "ปล่อยไว้แม้ปวดมาก"],
        "answer": "เอียงศีรษะให้น้ำไหลออก",
        "difficulty": "easy",
        "score": 1
    },
    {
        "q": "การว่ายน้ำบ่อยอาจเพิ่มความเสี่ยงโรคใด?",
        "choices": ["หูชั้นนอกอักเสบ", "ตับอักเสบ", "กระดูกพรุน", "ต้อกระจก"],
        "answer": "หูชั้นนอกอักเสบ",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "หูชั้นนอกอักเสบมักมีอาการใด?",
        "choices": ["ปวดหู คันหู เจ็บเมื่อดึงใบหู", "ปวดท้อง", "ไอเป็นเลือด", "ปัสสาวะแสบ"],
        "answer": "ปวดหู คันหู เจ็บเมื่อดึงใบหู",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "หากสงสัยแก้วหูทะลุ ไม่ควรทำอะไร?",
        "choices": ["หยอดยาเองโดยไม่ปรึกษาแพทย์", "พบแพทย์", "กันน้ำเข้าหู", "เล่าอาการให้แพทย์ฟัง"],
        "answer": "หยอดยาเองโดยไม่ปรึกษาแพทย์",
        "difficulty": "hard",
        "score": 3
    },
    {
        "q": "Tinnitus หมายถึงอะไร?",
        "choices": ["เสียงดังในหู เช่น วิ้ง ๆ", "หูชั้นนอกบวม", "ขี้หูเยอะ", "ใบหูแดง"],
        "answer": "เสียงดังในหู เช่น วิ้ง ๆ",
        "difficulty": "medium",
        "score": 2
    },
    {
        "q": "สาเหตุหนึ่งของเสียงวิ้งในหูคืออะไร?",
        "choices": ["เสียงดังสะสม", "กินผัก", "อ่านหนังสือ", "ตัดเล็บ"],
        "answer": "เสียงดังสะสม",
        "difficulty": "medium",
        "score": 2
    },
]

extra_health = [
    ("อาการใดควรระวังว่าอาจเป็นการสูญเสียการได้ยิน?", "ต้องให้คนพูดซ้ำบ่อย ๆ"),
    ("การตรวจการได้ยินมาตรฐานเรียกว่าอะไร?", "Audiometry"),
    ("Audiogram ใช้ประเมินอะไร?", "ระดับการได้ยินในแต่ละความถี่"),
    ("การอยู่คอนเสิร์ตใกล้ลำโพงควรใช้อะไร?", "ที่อุดหู"),
    ("หลังฟังเสียงดังแล้วหูอื้อชั่วคราวหมายถึงอะไร?", "หูได้รับเสียงมากเกินไป"),
    ("การเปิดหูฟังเสียงดังขณะอ่านหนังสือเป็นเวลานานเสี่ยงอะไร?", "หูตึงจากเสียงดัง"),
    ("หากมีหนองไหลจากหูควรทำอย่างไร?", "พบแพทย์"),
    ("การสูบบุหรี่เพิ่มความเสี่ยงอะไรในเด็ก?", "หูชั้นกลางอักเสบ"),
    ("ใบหูทำหน้าที่สำคัญอะไร?", "ช่วยรับและนำเสียง"),
    ("แก้วหูทำหน้าที่อะไร?", "สั่นสะเทือนเมื่อรับเสียง"),
    ("กระดูกหูชั้นกลางทำหน้าที่อะไร?", "ส่งต่อแรงสั่นสะเทือน"),
    ("คอเคลียอยู่ในหูชั้นใด?", "หูชั้นใน"),
    ("โรคเมเนียร์อาจมีอาการใด?", "เวียนศีรษะ หูอื้อ เสียงดังในหู"),
    ("เวลามีหวัดแล้วหูอื้อเกี่ยวข้องกับอะไร?", "ท่อยูสเตเชียนบวม"),
    ("การสั่งน้ำมูกแรงมากอาจทำให้เกิดอะไร?", "ความดันในหูเปลี่ยน"),
    ("หากแมลงเข้าหูควรทำอย่างไร?", "พบแพทย์ ไม่แหย่ลึก"),
    ("หากปวดหูร่วมกับไข้ควรทำอย่างไร?", "พบแพทย์"),
    ("การดำน้ำลึกเสี่ยงต่ออะไร?", "หูบาดเจ็บจากความดัน"),
    ("การขึ้นที่สูงเร็ว ๆ อาจทำให้หูอื้อเพราะอะไร?", "ความดันเปลี่ยน"),
    ("การใส่ earplug ที่ถูกต้องช่วยอะไร?", "ลดระดับเสียงที่เข้าสู่หู"),
    ("การพักหูหลังเสียงดังมีประโยชน์อย่างไร?", "ลดการรับเสียงสะสม"),
    ("การนอนหลับพอช่วยสุขภาพหูทางอ้อมอย่างไร?", "ช่วยลดความเครียดและการรับรู้อาการรบกวน"),
    ("ยาบางชนิดอาจมีผลต่ออะไร?", "การได้ยินหรือการทรงตัว"),
    ("ถ้ามีอาการหูตึงหลังได้รับยา ควรทำอย่างไร?", "แจ้งแพทย์"),
    ("เด็กที่เปิดวิดีโอเสียงดังใกล้หูเสี่ยงอะไร?", "ได้ยินลดลงจากเสียงดัง"),
    ("การตรวจหูด้วย otoscope ดูอะไร?", "ช่องหูและแก้วหู"),
    ("ขี้หูอุดตันอาจทำให้เกิดอะไร?", "หูอื้อ"),
    ("การล้างหูควรทำโดยใครเมื่อมีข้อบ่งชี้?", "บุคลากรสุขภาพ"),
    ("ถ้าเคยผ่าตัดหูควรระวังอะไร?", "ไม่หยอดยา/ล้างหูเอง"),
    ("เป้าหมายหลักของการดูแลหูคืออะไร?", "ป้องกันการสูญเสียการได้ยิน"),
    ("เสียงดังแบบเฉียบพลัน เช่น ระเบิดใกล้หู เสี่ยงอะไร?", "แก้วหูหรือหูชั้นในบาดเจ็บ"),
    ("อาการปวดหูหลังแคะหูอาจเกิดจากอะไร?", "ช่องหูถลอกหรือติดเชื้อ"),
    ("การใส่หูฟัง in-ear นานมากอาจเพิ่มอะไร?", "ความชื้นและการระคายเคืองในช่องหู"),
    ("หูฟังแบบครอบหูอาจปลอดภัยกว่าเมื่อใด?", "เมื่อใช้ระดับเสียงต่ำกว่าและไม่อุดลึก"),
    ("ถ้าต้องอยู่ในงานเสียงดังควรทำอะไรเป็นระยะ?", "พักหูออกจากบริเวณเสียงดัง"),
    ("การยืนใกล้ลำโพงในงานดนตรีควรหลีกเลี่ยงเพราะอะไร?", "เสียงเข้าหูรุนแรง"),
    ("การตรวจคัดกรองการได้ยินในนักศึกษามีประโยชน์อย่างไร?", "พบปัญหาเร็ว"),
    ("เสียงดังสะสมอันตรายเพราะอะไร?", "อาจค่อย ๆ ทำให้หูตึงโดยไม่รู้ตัว"),
    ("หากได้ยินไม่ชัดข้างเดียวร่วมกับเวียนศีรษะควรทำอย่างไร?", "พบแพทย์"),
    ("สุขภาพหูที่ดีช่วยเรื่องใดมากที่สุด?", "การเรียน การสื่อสาร และความปลอดภัย"),
]

while len(QUESTIONS) < 60:
    idx = len(QUESTIONS)
    question, correct = extra_health[(idx - 20) % len(extra_health)]
    QUESTIONS.append({
        "q": question,
        "choices": [correct, "แคะหูแรง ๆ", "ไม่ต้องสนใจเสมอ", "เปิดเพลงให้ดังขึ้น"],
        "answer": correct,
        "difficulty": ["easy", "medium", "hard"][idx % 3],
        "score": [1, 2, 3][idx % 3]
    })

# =====================
# B. Noise level 60 questions
# =====================
noise_items = [
    ("เสียงกระซิบประมาณกี่ dB?", "20-30 dB", ["20-30 dB", "60 dB", "90 dB", "120 dB"]),
    ("ห้องสมุดเงียบ ๆ ประมาณกี่ dB?", "30-40 dB", ["30-40 dB", "70 dB", "100 dB", "130 dB"]),
    ("การสนทนาปกติประมาณกี่ dB?", "ประมาณ 60 dB", ["ประมาณ 60 dB", "20 dB", "100 dB", "140 dB"]),
    ("เสียงจราจรหนาแน่นประมาณกี่ dB?", "80-90 dB", ["80-90 dB", "30 dB", "50 dB", "120 dB"]),
    ("เครื่องดูดฝุ่นประมาณกี่ dB?", "70-80 dB", ["70-80 dB", "20 dB", "110 dB", "150 dB"]),
    ("ไดร์เป่าผมประมาณกี่ dB?", "80-90 dB", ["80-90 dB", "30 dB", "50 dB", "130 dB"]),
    ("เครื่องปั่นอาหารประมาณกี่ dB?", "85-95 dB", ["85-95 dB", "40 dB", "60 dB", "120 dB"]),
    ("เครื่องตัดหญ้าประมาณกี่ dB?", "90 dB", ["90 dB", "40 dB", "60 dB", "130 dB"]),
    ("รถจักรยานยนต์เสียงดังประมาณกี่ dB?", "90-100 dB", ["90-100 dB", "40 dB", "60 dB", "130 dB"]),
    ("คอนเสิร์ตร็อกประมาณกี่ dB?", "100-110 dB", ["100-110 dB", "50 dB", "70 dB", "140 dB"]),
    ("ไนท์คลับประมาณกี่ dB?", "100-110 dB", ["100-110 dB", "40 dB", "60 dB", "130 dB"]),
    ("เสียงเชียร์กีฬาในสนามประมาณกี่ dB?", "95-105 dB", ["95-105 dB", "40 dB", "60 dB", "130 dB"]),
    ("เสียงประทัดใกล้ ๆ ประมาณกี่ dB?", "140-150 dB", ["140-150 dB", "60 dB", "90 dB", "110 dB"]),
    ("เสียงปืนประมาณกี่ dB?", "140-170 dB", ["140-170 dB", "60 dB", "90 dB", "110 dB"]),
    ("เสียงเครื่องบินขึ้นบินใกล้ ๆ ประมาณกี่ dB?", "120-140 dB", ["120-140 dB", "60 dB", "80 dB", "100 dB"]),
    ("ระดับ 85 dB ฟังได้ประมาณกี่ชั่วโมงต่อวันตามหลักอาชีวอนามัยทั่วไป?", "8 ชั่วโมง", ["8 ชั่วโมง", "4 ชั่วโมง", "1 ชั่วโมง", "15 นาที"]),
    ("ระดับ 88 dB ฟังได้ประมาณกี่ชั่วโมง?", "4 ชั่วโมง", ["4 ชั่วโมง", "8 ชั่วโมง", "1 ชั่วโมง", "15 นาที"]),
    ("ระดับ 91 dB ฟังได้ประมาณกี่ชั่วโมง?", "2 ชั่วโมง", ["2 ชั่วโมง", "8 ชั่วโมง", "4 ชั่วโมง", "15 นาที"]),
    ("ระดับ 94 dB ฟังได้ประมาณเท่าไร?", "1 ชั่วโมง", ["1 ชั่วโมง", "8 ชั่วโมง", "4 ชั่วโมง", "15 นาที"]),
    ("ระดับ 100 dB ฟังได้ประมาณเท่าไร?", "15 นาที", ["15 นาที", "1 ชั่วโมง", "4 ชั่วโมง", "8 ชั่วโมง"]),
]

for q, ans, choices in noise_items:
    QUESTIONS.append({
        "q": q,
        "choices": choices,
        "answer": ans,
        "difficulty": "medium",
        "score": 2
    })

more_noise = [
    ("เครื่องชงกาแฟ", "70-80 dB"),
    ("กาต้มน้ำไฟฟ้า", "50-70 dB"),
    ("รถเมล์", "80-90 dB"),
    ("รถไฟ", "90-100 dB"),
    ("รถไถนา", "90-100 dB"),
    ("เครื่องเจาะถนน", "100-110 dB"),
    ("ลำโพงงานวัด", "100-110 dB"),
    ("โรงอาหารช่วงเที่ยง", "75-85 dB"),
    ("ฟิตเนสเปิดเพลงดัง", "85-100 dB"),
    ("คลาสเต้น", "90-100 dB"),
    ("งานรับน้องเสียงดัง", "90-105 dB"),
    ("ร้านคาราโอเกะ", "90-105 dB"),
    ("เครื่องซักผ้า", "50-70 dB"),
    ("เครื่องอบผ้า", "60-70 dB"),
    ("เครื่องพิมพ์", "50-60 dB"),
    ("สนามฟุตบอลมีการเชียร์", "90-105 dB"),
    ("สนามบาสเกตบอลในร่ม", "80-95 dB"),
    ("โรงงานเสียงดัง", "85-100 dB"),
    ("เลื่อยยนต์", "110-120 dB"),
    ("เครื่องเป่าลม", "90-100 dB"),
    ("พลุ", "140-150 dB"),
    ("ฟ้าร้องใกล้ ๆ", "120 dB ขึ้นไป"),
    ("รถแข่ง", "120-130 dB"),
    ("Formula 1", "130 dB ขึ้นไป"),
    ("เครื่องบินรบ", "130-150 dB"),
    ("หูฟังเปิดสุด", "100 dB ขึ้นไป"),
    ("หูฟังระดับกลาง", "60-80 dB"),
    ("โรงภาพยนตร์บางช่วง", "80-100 dB"),
    ("ห้องสอบ", "30-40 dB"),
    ("ห้องอ่านหนังสือ", "30-40 dB"),
    ("ห้องประชุมทั่วไป", "50-70 dB"),
    ("เสียงฝนตกเบา ๆ", "40-50 dB"),
    ("เสียงนกร้อง", "40-60 dB"),
    ("เสียงตะโกนใกล้ ๆ", "85-95 dB"),
    ("เครื่องดูดฝุ่นแรงสูง", "80-90 dB"),
    ("สว่านไฟฟ้า", "90-100 dB"),
    ("เครื่องบดกาแฟ", "80-90 dB"),
    ("เสียงแตรรถใกล้ ๆ", "100-110 dB"),
    ("ไซเรนรถพยาบาลใกล้ ๆ", "110-120 dB"),
    ("รถไฟฟ้า", "80-90 dB"),
]

while len(QUESTIONS) < 120:
    idx = len(QUESTIONS) - 80
    label, ans = more_noise[idx % len(more_noise)]
    QUESTIONS.append({
        "q": f"{label} โดยทั่วไปมีระดับเสียงประมาณเท่าไร?",
        "choices": [ans, "20-30 dB", "50 dB", "160-180 dB"],
        "answer": ans,
        "difficulty": ["easy", "medium", "hard"][len(QUESTIONS) % 3],
        "score": [1, 2, 3][len(QUESTIONS) % 3]
    })

# =========================
# GITHUB FUNCTIONS
# =========================
def github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


def github_url():
    return f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{CSV_PATH}"


def empty_scores_df():
    return pd.DataFrame(columns=[
        "timestamp_bkk",
        "quiz_date",
        "day_no",
        "student_id",
        "score",
        "max_score",
        "correct_count",
        "question_ids"
    ])


def load_scores():
    url = github_url()
    r = requests.get(url, headers=github_headers(), params={"ref": BRANCH})

    if r.status_code == 404:
        return empty_scores_df(), None

    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")

    if not content.strip():
        return empty_scores_df(), data.get("sha")

    df = pd.read_csv(StringIO(content), dtype={"student_id": str})

    # Backward compatibility if an older CSV is missing some columns
    required_cols = empty_scores_df().columns.tolist()
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    return df[required_cols], data["sha"]


def save_scores(df, sha):
    csv_text = df.to_csv(index=False)
    content_b64 = base64.b64encode(csv_text.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"update ear quiz scores {datetime.now(BKK).strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content_b64,
        "branch": BRANCH
    }

    if sha:
        payload["sha"] = sha

    r = requests.put(github_url(), headers=github_headers(), data=json.dumps(payload))
    r.raise_for_status()


# =========================
# QUIZ FUNCTIONS
# =========================
def get_today_questions():
    today = datetime.now(BKK).date()
    day_no = (today - START_DATE).days + 1

    if day_no < 1:
        day_no = 1

    total_days = len(QUESTIONS) // 2
    day_index = (day_no - 1) % total_days

    q1 = day_index * 2
    q2 = q1 + 1

    return today, day_no, [q1, q2]


def normalize_student_id(student_id):
    return student_id.strip()


def is_correct(q, user_answer):
    correct_answers = q.get("answers", [q["answer"]])
    return user_answer in correct_answers


# =========================
# UI
# =========================
st.title("👂 Ear Health Quiz: KU KPS Infirmary")
st.caption("ตอบคำถามสุขภาพหูวันละ 2 ข้อ สะสมคะแนนชิงรางวัล")

today, day_no, q_ids = get_today_questions()

try:
    df, sha = load_scores()
except Exception as e:
    st.error("โหลดข้อมูลคะแนนจาก GitHub ไม่สำเร็จ")
    st.exception(e)
    st.stop()

st.info(f"วันนี้: {today.strftime('%d/%m/%Y')} | วันที่เล่นลำดับที่ {day_no}")

student_id = st.text_input("กรอก Student ID ทุกครั้งที่เข้าเล่น", max_chars=30)

if not student_id:
    st.warning("กรุณากรอก Student ID เพื่อเริ่มเล่น")
    st.stop()

sid = normalize_student_id(student_id)

if len(sid) < 3:
    st.warning("กรุณากรอก Student ID ให้ถูกต้อง")
    st.stop()

# ensure dtype safety
df["student_id"] = df["student_id"].astype(str)
df["quiz_date"] = df["quiz_date"].astype(str)
df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)

played_today = (
    (df["quiz_date"] == str(today)) &
    (df["student_id"] == sid)
).any()

my_total = int(df[df["student_id"] == sid]["score"].sum()) if not df.empty else 0

if not df.empty:
    leaderboard = (
        df.groupby("student_id")["score"]
        .sum()
        .sort_values(ascending=False)
    )
    top_score = int(leaderboard.iloc[0]) if len(leaderboard) > 0 else 0
else:
    top_score = 0

col1, col2 = st.columns(2)
with col1:
    st.metric("คะแนนสะสมของคุณ", my_total)
with col2:
    st.metric("คะแนนสูงสุดสะสมถึงวันนี้", top_score)

if played_today:
    st.success("วันนี้คุณเล่นแล้ว กรุณากลับมาเล่นใหม่วันถัดไป")
    st.stop()

st.subheader("คำถามของวันนี้")

answers = {}
max_score = 0

with st.form("quiz_form"):
    for n, qid in enumerate(q_ids, start=1):
        q = QUESTIONS[qid]
        st.markdown(f"### ข้อ {n}: {q['q']}")
        st.caption(f"ระดับ: {q['difficulty']} | คะแนน: {q['score']}")

        answers[qid] = st.radio(
            "เลือกคำตอบ",
            q["choices"],
            key=f"q_{qid}",
            index=None
        )

        max_score += int(q["score"])

    submitted = st.form_submit_button("ส่งคำตอบ")

if submitted:
    if any(v is None for v in answers.values()):
        st.warning("กรุณาตอบให้ครบทั้ง 2 ข้อ")
        st.stop()

    score = 0
    correct_count = 0

    for qid, user_ans in answers.items():
        q = QUESTIONS[qid]
        if is_correct(q, user_ans):
            score += int(q["score"])
            correct_count += 1

    new_row = {
        "timestamp_bkk": datetime.now(BKK).strftime("%Y-%m-%d %H:%M:%S"),
        "quiz_date": str(today),
        "day_no": day_no,
        "student_id": sid,
        "score": score,
        "max_score": max_score,
        "correct_count": correct_count,
        "question_ids": ",".join(map(str, q_ids))
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    try:
        save_scores(df, sha)
    except Exception as e:
        st.error("บันทึกคะแนนไป GitHub ไม่สำเร็จ")
        st.exception(e)
        st.stop()

    st.success(f"คุณได้ {score}/{max_score} คะแนน ตอบถูก {correct_count}/2 ข้อ")

    st.subheader("เฉลย")
    for qid, user_ans in answers.items():
        q = QUESTIONS[qid]
        mark = "✅" if is_correct(q, user_ans) else "❌"
        st.write(f"{mark} {q['q']}")
        st.write(f"คำตอบของคุณ: {user_ans}")
        st.write(f"เฉลย: **{q['answer']}**")

    st.balloons()
    st.rerun()
