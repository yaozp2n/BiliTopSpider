#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   BiliSipder.py
@Time    :   2022/06/22 16:42:43
@Author  :   Yao Zipeng 
@Version :   python 3.8
爬取b站排行榜视频和弹幕
'''
from pyquery import PyQuery as pq
import requests
import time
import re
import json
import subprocess


class BiliSpider(object):
    def __init__(self):
        self.url = 'https://www.bilibili.com/v/popular/rank/all'
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'referer': 'https://www.bilibili.com/',
        }

    def get_data(self, url):
        print('scraping %s...' % url)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.content
            print(response.status_code)
        except requests.RequestException:
            print('error occurred while scraping %s' % self.url)

    def pase_data(self, data):
        data = data.decode()
        doc = pq(data)
        elements = doc('.rank-item')
        for element in elements.items():
            items = {}
            items['title'] = element('.title').text()
            items['link'] = element('.title').attr(
                'href').replace('//', 'https://')
            items['up'] = element('.up-name').text()
            items['paly'] = element(
                '.detail-state .data-box').text().split()[0]
            items['like'] = element(
                '.detail-state .data-box').text().split()[1]
            yield items

    def get_video_data(self, html_data):
        """解析视频数据"""

        html_data = html_data.decode()
        # 提取视频的标题
        doc = pq(html_data)
        title = doc('.video-title.tit').text()
        # print(title)

        # 提取视频对应的json数据
        json_data = re.findall(
            '<script>window\.__playinfo__=(.*?)</script>', html_data)[0]
        # print(json_data)  # json_data 字符串
        json_data = json.loads(json_data)
        # pprint.pprint(json_data)

        # 提取音频的url地址
        audio_url = json_data['data']['dash']['audio'][0]['backupUrl'][0]
        print('解析到的音频地址:', audio_url)

        # 提取视频画面的url地址
        video_url = json_data['data']['dash']['video'][0]['backupUrl'][0]
        print('解析到的视频地址:', video_url)

        video_data = [title, audio_url, video_url]
        return video_data

    def save_data(self, file_name, audio_url, video_url):
        # 请求数据
        print('正在请求音频数据')
        audio_data = self.get_data(audio_url)
        print('正在请求视频数据')
        video_data = self.get_data(video_url)
        with open(file_name + '.mp3', mode='wb') as f:
            f.write(audio_data)
            print('正在保存音频数据')
        with open(file_name + '.mp4', mode='wb') as f:
            f.write(video_data)
            print('正在保存视频数据')

    def merge_data(self, video_name):
        print('视频合成开始:', video_name)
        # ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -strict experimental output.mp4
        COMMAND = f'ffmpeg -i {video_name}.mp4 -i {video_name}.mp3 -c:v copy -c:a aac -strict experimental {video_name}_output.mp4'
        subprocess.Popen(COMMAND, shell=True)
        print('视频合成结束:', video_name)

    def run(self):
        # 1.发送请求，获取响应
        data = self.get_data(self.url)
        # 2.解析数据
        items = self.pase_data(data)
        for item in items:
            # print(item['link'])
            data = self.get_data(item['link'])
            file_name = self.get_video_data(data)[0]
            audio_url = self.get_video_data(data)[1]
            video_url = self.get_video_data(data)[2]
            self.save_data(file_name, audio_url, video_url)
            self.merge_data(file_name)
            time.sleep(1)
            break


if __name__ == '__main__':
    bili = BiliSpider()
    bili.run()
