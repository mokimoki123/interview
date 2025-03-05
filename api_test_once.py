
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4")

import yaml
import os
import tools
import random

import argparse
import numpy as np

from log_config import setup_logging  


args = argparse.ArgumentParser()
args.add_argument('config_path', type=str, default=None, help='config_path')

args = args.parse_args()

config = yaml.load(open(args.config_path, 'r', encoding='UTF-8'), Loader=yaml.FullLoader)

logger = setup_logging(config['log_dir'])





class Test_once():

    def __init__(self, config) -> None:
        ### 导入所有api
        apis = config["apis"]
        self.all_api_instances = []
        for api in apis:
            ### 构建实例
            api_config = apis[api]
            api_config['name'] = api
            api_files = tools.import_module_by_name(api_config['api_class'][0])
            api_cls = getattr(api_files, api_config['api_class'][1])
            del api_config['api_class']
            api_instance = api_cls(**api_config)

            ### 实例试运行
            # flag = api_instance.test(logger)
            flag = True
            if not flag:
                logger.warning(f"api {api} test failed")
            else:
                logger.info(f"api {api} test passed")
                self.all_api_instances.append(api_instance)
        
        ## 导入测试数据集
        datasets = config["datasets"]
        self.load_interference_data()
        self.all_dataset = []
        for dataset in open(datasets, encoding='utf-8').readlines():
            self.all_dataset.append(dataset.strip())
        logger.info(f"len of all_dataset: {len(self.all_dataset)}")

        ## 确定非压力评测时随机选取的测试数据集数量
        self.prompt_quantity = config["prompt_quantity"]

    def test_all_indicator(self):
        ### 跑所有测试指标
        self.test_api_latency()

        ### 输出平均值：
        for api_instance in self.all_api_instances:
            try:
                logger.info(f"average RT of {api_instance.name}: {np.mean(api_instance.RT)}")
                logger.info(f"average FTT of {api_instance.name}: {np.mean(api_instance.FTT)}")
                logger.info(f"average TPS of {api_instance.name}: {np.mean(api_instance.TPS)}")
                if 'ANTT' in api_instance.__dict__:
                    logger.info(f"average ANTT of {api_instance.name}: {np.mean(api_instance.ANTT)}")
            except:
                logger.warning(f"average RT of {api_instance.name} failed")
        
        ### 画图

    ### 加载小说作为干扰数据集
    def load_interference_data(self):
        ### 加载数据 
        txt_file = open('斗罗大陆.txt', 'r', encoding='utf-8')
        all_txt = ''
        for line in txt_file:
            all_txt += line.replace(" ","")
        self.interference_dataset = all_txt
        self.interference_dataset_len = len(self.interference_dataset)
        # print(self.dataset)
    
    def get_interference_data_once(self, lens):
        randon_start = random.randint(0, self.interference_dataset_len - lens)
        dataset = self.interference_dataset[randon_start:randon_start+lens]

        new_lens = lens
        while True:
            len_dataset = len(enc.encode(dataset)) 
            if abs(len_dataset -lens) <= 10:
                break
            else:
                new_lens = new_lens + lens - len_dataset
                randon_start = random.randint(0, self.interference_dataset_len - new_lens)
                dataset = self.interference_dataset[randon_start:randon_start+new_lens]
        # print(len(enc.encode(dataset)) )
        return dataset


    def test_api_latency(self):
        logger.info("test_api_latency 被调用")
        ### 测试api的延迟
        prompts = random.choices(self.all_dataset, k=self.prompt_quantity)
        interference_data_lens = [500, 1000, 2000]
Ƒ
        error_msg = ''
        for test_index, prompt in enumerate(prompts):
            interference_data = self.get_interference_data_once(interference_data_lens[test_index])
            prompt = interference_data + '。请忽略前面内容，请忽略前面内容，请忽略前面内容，并用中文回答以下问题：' + prompt
            logger.info(f"prompt: {prompt}")
            for api_instance in self.all_api_instances:
                logger.info(f"testing api {api_instance.name}")
                try:
                    response = api_instance.call_api_latency_test(prompt, logger)
                    
                    if response == False:
                        logger.warning(f"api {api_instance.name} failed")
                        continue
                    start_time = response["start_time"]
                    FTT = response["result_times"][0] - start_time
                    end_time = response["end_time"]
                    token_number = response["token_number"]
                    RT = end_time - start_time
                    TPS = token_number / (RT - FTT)
                    results = ""
                    for result in response["results"]:
                        results += result.replace("\n","")
                    if 'create_times' in response:
                        create_times = response["create_times"]
                        ANTT = np.mean(response["result_times"]) - np.mean(create_times)
                except Exception as e:
                    print(e)
                    logger.info(e)
                    error_msg = error_msg + 'Error while test: ' + api_instance.name + '\n'
                    logger.info(f"Error while test: {api_instance.name}")
                    # api_instance.RT.append(1000)
                    # api_instance.FTT.append(1000)
                    # api_instance.TPS.append(0)
                    # api_instance.ANTT.append(1000)
                    api_instance.results.append('error')
                    continue


                logger.info(f"start_time: {start_time}")
                logger.info(f"first_token_time: {FTT}")
                logger.info(f"response time: {RT}")
                logger.info(f"token per second: {TPS}")
                logger.info(f"network transmission time: {ANTT}")
                logger.info(f"results: {results}")

                api_instance.RT.append(RT)
                api_instance.FTT.append(FTT)
                api_instance.TPS.append(TPS)
                api_instance.ANTT.append(ANTT)
                api_instance.results.append(results)
        
        if len(error_msg) !=0:
            tools.send_email(error_msg)


test_ins = Test_once(config)
test_ins.test_all_indicator()