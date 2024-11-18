from django.shortcuts import render
from django.shortcuts import render, HttpResponse
import pandas as pd
from io import BytesIO
# Create your views here.



# Create your views here.

def input_index(request):
    return render(request, "autoinput/autoinputindex.html")

def combine_files(request):
    if request.method == "POST":
        file = request.FILES.get("health_input")
        건강2 = pd.read_excel(file)
        건강2.rename(columns= {"성명" : "근로자명"} , inplace=True) # 성함 열 근로자명으로 열 이름 바꾸기
        건강2.rename(columns= {"주민등록번호" : "생년월일"} , inplace=True) # 주민번호 열 생년월일으로 열 이름 바꾸기
        건강2["생년월일"] = 건강2["생년월일"].str[: -8] # 생년월일 양식 통일(주민번호 뒷자리 삭제)
        건강2 = 건강2.set_index(["근로자명", "생년월일"]) # 인덱스 처리     
        건강기본 = 건강2.iloc[: , -1 : ].copy()
        건강기본["개인부담금"] = 건강기본.가입자총납부할보험료 # 개인부담금 열 생성
        건강기본["사업주부담금"] = 건강기본.가입자총납부할보험료 # 사업주부담금 열 생성
        건강기본.drop(columns = ["가입자총납부할보험료"], inplace=True) # 불필요한 열 삭제

        file2 = request.FILES.get("national_input")
        aaa = pd.read_excel(file2) # 국민연금 세팅
        aaa.rename(mapper = {"가입자명" : "근로자명"}, axis="columns", inplace=True)
        aaa.rename(mapper = {"주민번호" : "생년월일"}, axis="columns", inplace=True)
        aaa["생년월일"] = aaa["생년월일"].str[: -8]
        국민기본 = aaa.set_index(["근로자명", "생년월일"]) # 인덱스 처리
        국민기본 = 국민기본.iloc[: , -1 : ].copy()
        국민기본["개인부담금"] = 국민기본.결정보험료/2 # 개인부담금 열 생성
        국민기본["사업주부담금"] = 국민기본.결정보험료/2 # 사업주부담금 열 생성
        국민기본.drop(columns = ["결정보험료"], inplace=True) # 불필요한 열 삭제

        file3 = request.FILES.get("employ_input")
        고용기본 = pd.read_excel(file3,header = 1, thousands = ",") # 고용보험 기본 세팅
        생년월일통일 = 고용기본["생년월일"].replace("-", "", inplace = True, regex = True) # 생년월일 양식 통일
        고용기본 = 고용기본.set_index(["근로자명", "생년월일"]) # 근로자명, 생년월일 인덱스 처리
        # 생년월일통일 = 고용기본.columns = ["근로자명", "생년월일", "근로자실업급여보험료.3", "사업주실업급여보험료.3", "사업주고안직능보험료.3"] 22개 22개로 맞춰야 대서 안댄다
        고용기본2 = 고용기본.iloc[: , -3 : ].copy()
        고용기본2.columns = ["개인부담금_고용", "사업주실업급여보험료", "사업주고안직능보험료"] # 고용보험 열 이름 변경
        고용기본2["사업주부담금"] = 고용기본2.사업주실업급여보험료 + 고용기본2.사업주고안직능보험료 # 고용보험 사업주부담금 열 생성
        고용기본2.drop(columns = ["사업주실업급여보험료", "사업주고안직능보험료"], inplace=True) # 고용보험 불필요열 삭제

        file4 = request.FILES.get("industrial_input")
        산업 = pd.read_excel(file4) # 산재 기본 세팅
        주민번호통일 = 산업["생년월일"].replace("-", "", inplace = True, regex = True) # 생년월일 양식 통일
        산업기본 = 산업.set_index(["근로자명", "생년월일"]) # 근로자명, 생년월일 인덱스처리
        산업기본2 = 산업기본.iloc[: , -1 : ].copy() # 열 하나만 가져온다
        산업기본2.columns = ["사업주부담금"] # 가져온 열 이름 변경
    
        건강국민 = 건강기본.merge(국민기본, how = "outer", on = ["근로자명", "생년월일"], suffixes= ("_건강", "_국민"), indicator= True ) # 건강보험, 국민연금 파일 합치기
        건강국민.drop(columns = ["_merge"], inplace=True) # 불필요한 열 삭제
        건강국민 = 건강국민.fillna(0) # Nan 값 0으로 교체
        고용산재2= 고용기본2.merge(산업기본2, how = "outer", on = ["근로자명", "생년월일"], suffixes= ("_고용", "_산재"), indicator= True ) # 고용보험, 산재보험 합치기
        고용산재2.drop(columns = ["_merge"], inplace=True) # 불필요한 열(merge) 삭제
        고용산재2 = 고용산재2.fillna(0)
        건강국민고용산재 = 건강국민.merge(고용산재2, how = "outer", on = ["근로자명", "생년월일"], suffixes= ("_건강", "_국민"), indicator= True ) # 4대보험 파일 합치기
        건강국민고용산재.drop(columns = ["_merge"], inplace=True) # 불필요한 열 삭제
        건강국민고용산재 = 건강국민고용산재.fillna(0) # Nan값 0으로 교체
        건강국민고용산재["사업주부담금합"] = 건강국민고용산재.사업주부담금_건강 + 건강국민고용산재.사업주부담금_국민 + 건강국민고용산재.사업주부담금_고용 + 건강국민고용산재.사업주부담금_산재 # 개인별 4대보험 사업주부담금 열 만들기
        건강국민고용산재 = 건강국민고용산재.sort_index() # 각 행을 근로자명 내림차순 배열
        건강국민고용산재.reset_index(inplace = True) # 인덱스 행 초기화
        건강국민고용산재["직종"] = "" # 직종열 생성(빈 칸임)
        건강국민고용산재 = 건강국민고용산재.reindex(columns = ['직종', '근로자명', '생년월일', '개인부담금_건강', '사업주부담금_건강', '개인부담금_국민', '사업주부담금_국민',
        '개인부담금_고용', '사업주부담금_고용', '사업주부담금_산재', '사업주부담금합']) # 열 순서 변경(직종을 맨 앞으로)
        with BytesIO() as b:
            writer = pd.ExcelWriter(b, engine="openpyxl")
            건강국민고용산재.to_excel(writer, sheet_name="sample_sheet")
            writer.close()
            response_data2 = b.getvalue()

        return HttpResponse(
        response_data2,
           content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    return render(request, "autoinput/autoinput001.html")