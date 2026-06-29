FROM python:3.11-slim
WORKDIR /app
# gcc/libpq-dev 编译 psycopg；其余为 WeasyPrint 运行库（PDF 导出），
# fonts-noto-cjk 保证中文简历 PDF 不乱码。
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     gcc libpq-dev \
     libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
     libffi-dev libcairo2 fonts-noto-cjk \
  && rm -rf /var/lib/apt/lists/*
# 先拷全部源码再装：editable 安装（packages=["src"]）要求 src 目录存在
COPY . .
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e ".[dev]"
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "."]
