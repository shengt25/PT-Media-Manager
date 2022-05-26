import requests
import json
from src.utils import write_log


class WeCom:
    def __init__(self, corp_id, secret, agent_id):
        self.base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        self.corp_id = corp_id
        self.secret = secret
        self.agent_id = agent_id
        self.token = self._get_token()

    def _get_token(self):
        arg_url = "/gettoken?corpid={}&corpsecret={}".format(self.corp_id, self.secret)
        url = self.base_url + arg_url
        try:
            r = requests.get(url)
            js = json.loads(r.text)
            return js["access_token"]
        except:
            write_log("[error] CWeChat CorpWechat._get_token Get access-token failed")

    def _get_media_id(self, msg_type, file_obj):
        arg_url = "/media/upload?access_token={}&type={}".format(self.token, msg_type)
        url = self.base_url + arg_url
        data = {"media": file_obj}
        try:
            r = requests.post(url=url, files=data)
            js = r.json()
            return js["media_id"]
        except:
            write_log("[error] CWeChat CorpWechat._get_media_id Get media_id failed")

    def _gen_msg(self, touser, msg_type, contents, file_obj):
        base_string = """{
        "touser": touser, 
        "msgtype": msg_type, 
        "agentid": self.agent_id, 
        msg_type: {"%s": "%s"},
        "safe": 0}"""
        if msg_type == "text":
            values = base_string % ("content", contents)
        else:
            media_id = self._get_media_id(msg_type, file_obj)
            values = base_string % ("media_id", media_id)
        data = eval(values)
        js = json.dumps(data)
        to_bytes = bytes(js, "utf-8")
        return to_bytes

    def send_message(self, wecom_id, msg_type, max_retry_times=10, contents="", file_obj=None):
        retry_times = 0
        while True:
            self.token = self._get_token()
            post_msg = self._gen_msg(wecom_id, msg_type, contents, file_obj)
            arg_url = "/message/send?access_token={}".format(self.token)
            url = self.base_url + arg_url
            try:
                response = requests.post(url, data=post_msg)
                write_log("[info] CWeChat CorpWechat.send_message Successfully post data to wechat: " + str(response))
            except Exception as e:
                if retry_times >= max_retry_times:
                    write_log("[error] exceed max retry times, abort")
                    break
                write_log("[error] CWeChat CorpWechat.send_message Error post data to wechat " + str(e))
                retry_times += 1
            else:
                break

    def update_token(self):
        # token would expire every 2 hours, update in time!
        # https://work.weixin.qq.com/api/doc/90000/90135/91039
        self.token = self._get_token()


"""
how to:

# send text message
alert_wechat.send_message(wechat_id, msg_type="text", contents="str")

# send local image message
alert_wechat.send_message(wechat_id, msg_type="image", file_obj=open(image_path, "rb"))

# send local video message
alert_wechat.send_message(wechat_id, msg_type="video", file_obj=open(video_path, "rb")

# send local file message
alert_wechat.send_message(wechat_id, msg_type="file", file_obj=open(file_path, "rb"))
"""
