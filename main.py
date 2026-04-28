import os
import json
import datetime
import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

# 한글 폰트 설정 (윈도우 기준)
matplotlib.rc('font', family='Malgun Gothic')

class PocketGuardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PocketGuard: 초간단 스마트 가계부")
        self.geometry("1100x750")
        
        self.db_file = "expenses.json"
        self.data = self.load_data()

        # UI 레이아웃
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # 왼쪽: 입력 패널
        self.input_frame = ctk.CTkFrame(self, width=400, corner_radius=15)
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.init_input_panel()

        # 오른쪽: 통계 및 그래프 패널
        self.stats_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.stats_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.init_stats_panel()

    def load_data(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_data(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def init_input_panel(self):
        ctk.CTkLabel(self.input_frame, text="💰 빠른 지출 기록", font=("Arial", 22, "bold")).pack(pady=30)

        ctk.CTkLabel(self.input_frame, text="금액 입력", font=("Arial", 14)).pack(pady=(10, 0))
        self.entry_amount = ctk.CTkEntry(self.input_frame, placeholder_text="숫자만 입력 (예: 5000)", font=("Arial", 18), height=45)
        self.entry_amount.pack(padx=30, pady=10, fill="x")

        ctk.CTkLabel(self.input_frame, text="카테고리 선택", font=("Arial", 14)).pack(pady=(20, 0))
        
        categories = ["카페", "학교", "고정지출", "이벤트", "식당", "간식", "기타"]
        self.cat_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.cat_frame.pack(pady=10)

        for i, cat in enumerate(categories):
            r, c = i // 2, i % 2
            btn = ctk.CTkButton(self.cat_frame, text=cat, width=140, height=40, 
                                fg_color="#3B3B3B", hover_color="#555555",
                                command=lambda c=cat: self.add_expense(c))
            btn.grid(row=r, column=c, padx=5, pady=5)

        # 최근 내역 간략 보기
        ctk.CTkLabel(self.input_frame, text="오늘의 총 지출", font=("Arial", 14)).pack(pady=(30, 0))
        self.lbl_today_total = ctk.CTkLabel(self.input_frame, text="0원", font=("Arial", 24, "bold"), text_color="#A9D08E")
        self.lbl_today_total.pack()
        self.update_today_total()

    def init_stats_panel(self):
        # 탭 뷰 (그래프 종류 선택)
        self.tabview = ctk.CTkTabview(self.stats_frame)
        self.tabview.pack(fill="both", expand=True)

        self.tab_pie = self.tabview.add("📊 카테고리별 비중")
        self.tab_bar = self.tabview.add("📈 지출 추이 비교")

        self.btn_refresh = ctk.CTkButton(self.stats_frame, text="그래프 업데이트", command=self.update_graphs)
        self.btn_refresh.pack(pady=10)

        self.update_graphs()

    def add_expense(self, category):
        amount_str = self.entry_amount.get().strip()
        if not amount_str.isdigit():
            messagebox.showwarning("경고", "금액란에 숫자만 입력해주세요.")
            return

        new_entry = {
            "amount": int(amount_str),
            "category": category,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }

        self.data.append(new_entry)
        self.save_data()
        self.entry_amount.delete(0, "end")
        self.update_today_total()
        self.update_graphs()
        messagebox.showinfo("완료", f"{category} 항목에 {amount_str}원이 기록되었습니다.")

    def update_today_total(self):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        total = sum(item["amount"] for item in self.data if item["date"] == today)
        self.lbl_today_total.configure(text=f"{total:,}원")

    def update_graphs(self):
        self.draw_pie_chart()
        self.draw_bar_chart()

    def draw_pie_chart(self):
        for child in self.tab_pie.winfo_children(): child.destroy()
        
        if not self.data: return

        cat_totals = {}
        for item in self.data:
            cat = item["category"]
            cat_totals[cat] = cat_totals.get(cat, 0) + item["amount"]

        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor('#2B2B2B')
        ax.set_facecolor('#2B2B2B')
        
        wedges, texts, autotexts = ax.pie(cat_totals.values(), labels=cat_totals.keys(), autopct='%1.1f%%',
                                          textprops={'color':"w"}, startangle=140)
        ax.set_title("카테고리별 지출 비율", color="w")

        canvas = FigureCanvasTkAgg(fig, master=self.tab_pie)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def draw_bar_chart(self):
        for child in self.tab_bar.winfo_children(): child.destroy()
        
        if not self.data: return

        # 최근 7일간 추이
        date_totals = {}
        for i in range(6, -1, -1):
            d = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%m-%d")
            date_totals[d] = 0

        for item in self.data:
            d_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
            d_str = d_obj.strftime("%m-%d")
            if d_str in date_totals:
                date_totals[d_str] += item["amount"]

        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor('#2B2B2B')
        ax.set_facecolor('#2B2B2B')
        
        ax.bar(date_totals.keys(), date_totals.values(), color="#2FA572")
        ax.set_title("최근 7일 지출 추이", color="w")
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

        canvas = FigureCanvasTkAgg(fig, master=self.tab_bar)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    app = PocketGuardApp()
    app.mainloop()
