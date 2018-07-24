# -*- coding: utf-8 -*-
import scrapy
from PIL import Image
import requests
import re
from aip import AipOcr

class DoubanSpiderSpider(scrapy.Spider):
    name = 'douban_spider'
    allowed_domains = ['douban.com']
    start_urls = ['https://movie.douban.com/top250']
    # 登录接口
    login_url = 'https://www.douban.com/accounts/login'
    formEmail = 'formEmail'
    formPassword = 'formPassword'
    # 主页面 用于获取captcha_id
    main_url = 'https://www.douban.com/'
    # 百度图片识别
    APP_ID = 'APP_ID'
    API_KEY = 'API_KEY'
    SECRET_KEY = 'SECRET_KEY'
    AipOcrClient = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    # 正则 用于剔除百度图片识别的多余的部分
    pattern = re.compile(r'\w{3,}')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0"}

    def start_requests(self):
        return [scrapy.FormRequest("https://accounts.douban.com/login", headers=DoubanSpiderSpider.headers,
                                   meta={"cookiejar": 1},
                                   callback=self.parse_before_login)]

    def parse_before_login(self, response):
        captcha_id = response.xpath('//input[@name="captcha-id"]/@value').extract_first()
        captcha_image_url = response.xpath('//img[@id="captcha_image"]/@src').extract_first()
        if captcha_image_url is None:
            formdata = {
                "source": "index_nav",
                "form_email": DoubanSpiderSpider.formEmail,
                "form_password": DoubanSpiderSpider.formPassword,
            }
        else:
            save_image_path = "./captcha.jpeg"
            result = requests.get(captcha_image_url)
            with open(save_image_path, 'wb') as f:
                f.write(result.content)
            image = self.get_file_content(save_image_path)
            parseImgResult = DoubanSpiderSpider.AipOcrClient.basicGeneral(image)
            print("parseImgResult: %s" % parseImgResult)
            words_result = parseImgResult['words_result']
            if len(words_result) == 0:
                try:
                    im = Image.open(save_image_path)
                    im.show()
                except:
                    pass
                captcha_solution = input('根据打开的图片输入验证码:')
            else:
                captcha_solution = DoubanSpiderSpider.pattern.search(words_result[0]['words']).group()
            print("captcha_solution: %s" % captcha_solution)
            formdata = {
                "source": "None",
                "redir": "https://www.douban.com",
                "form_email": DoubanSpiderSpider.formEmail,
                "form_password": DoubanSpiderSpider.formPassword,
                "captcha-solution": captcha_solution,
                "captcha-id": captcha_id,
                "login": "登录",
            }
            print("captcha_id: %s" % captcha_id)
            print("captcha_solution: %s" % captcha_solution)
        print("登录中")
        # 提交表单
        return scrapy.FormRequest.from_response(response, meta={"cookiejar": response.meta["cookiejar"]},
                                                formdata=formdata,
                                                callback=self.parse_after_login)

    def parse_after_login(self, response):
        print('parse_after_login')
        account = response.xpath('//a[@class="bn-more"]/span/text()').extract_first()
        if account is None:
            print("登录失败")
        else:
            print(u"登录成功,当前账户为 %s" % account)
        yield from super().start_requests()

    def get_file_content(self, filePath):
        with open(filePath, 'rb') as f:
            return f.read()

    def parse(self, response):
        print("parse")

