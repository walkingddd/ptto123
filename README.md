# PT文件转存123网盘工具


## 1. 项目简介
该工具旨在解决运营商对用户上传带宽日益限制的问题。当需要将从PT站点下载的文件转存到123网盘时，传统上传方式会占用用户自身的上传带宽，而本工具通过调用123网盘的秒传接口实现文件快速转存，若秒传失败则自动休眠一段时间后重试，从而避免用户进行首次上传（首传），最大程度节省上传带宽资源。


## 2. 核心功能
1. **秒传机制**：优先调用123网盘秒传接口（非openapi，规避openapi仅支持10G以下文件的限制），直接基于文件哈希信息完成转存，无需实际上传文件内容
2. **智能重试**：当秒传失败时，自动休眠一段时间后重新尝试秒传，提高转存成功率
3. **带宽节省**：通过避免用户执行文件首传，显著减少对本地上传带宽的占用


## 3. 部署方法
使用Docker Compose快速部署，配置如下：

```yaml
version: '3'

services:
  p123client-service:
    image: walkingd/ptto123:latest  # 使用您构建的镜像
    container_name: ptto123
    environment:
      # 123网盘的账号，注意非openapi，因为openapi限制只能秒传10G以下的文件
      - ENV_123_PASSPORT=     
      # 123网盘的密码
      - ENV_123_PASSWORD=
      # 上传目标目录ID，指定文件上传到123网盘的哪个目录的目录ID，可以从浏览器获得
      - UPLOAD_TARGET_PID=0      
    volumes:
      # MP将文件转移到/vol3/1000/Video/MoviePilot/transfer，映射到/app/upload，程序会监控/app/upload有无新文件
      - /vol3/1000/Video/MoviePilot/transfer:/app/upload

    restart: always  # 设置容器自动重启策略
```


## 4. 注意事项
- 环境变量`ENV_123_PASSPORT`和`ENV_123_PASSWORD`需替换为用户本人的123网盘登录账号和密码（使用非openapi方式，以避免10G以下文件的限制）
- `UPLOAD_TARGET_PID`需替换为123网盘中目标存储目录的ID（可通过123网页版进入目标目录，从URL中提取）
- 本地映射目录需包含待转存的PT文件，工具会自动监控该目录并处理文件转存
