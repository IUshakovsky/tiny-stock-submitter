import click
import keyring
import json
import logging

from typing import Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class Submitter():
    def __init__(self) -> None:
        self.log = logging.getLogger('log')
        self.log.setLevel(logging.INFO)
        file_handler = logging.FileHandler('./tss.log')
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:: %(message)s')
        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)
    
    def run(self) -> None:
        try:
            self.driver = webdriver.Chrome()
            auth_data = self.get_auth_data()
            self.authenticate(auth_data=auth_data) 
            if self.check_captcha():
                self.submit()
            self.driver.close()
              
        except Exception as ex:
            click.echo('Error, check tss.log')   
            self.log.exception(ex)
            self.driver.close()             
    
    def get_auth_data(self) -> Tuple:
        login = self.get_login()
        passwd = keyring.get_password(self.stock, login)
        if not passwd:
            passwd = self.set_passwd(login)
        return (login,passwd)
            
    def get_login(self) -> str:
        with open('tss.json') as conf_file:
            self.config = json.load(conf_file)
         
        if self.stock in self.config:  
            return self.config[self.stock]
        else:
            return self.set_login()
    
    def set_login(self) -> str:
        new_login = click.prompt(f'Enter login')
        self.config[self.stock] = new_login
        with open('tss.json','w') as conf_file:
            json.dump(self.config, conf_file)    
        return new_login
    
    def set_passwd(self, login:str) -> str:
        passwd = click.prompt(f'Enter password',hide_input=True)
        keyring.set_password(self.stock, login, passwd)
        return passwd
    
    def authenticate(self, auth_data:Tuple) -> None:
        self.driver.get(self.login_page)
    
    def submit(self) -> None:
        pass
        
    def check_captcha(self):
        return True
    
class CanStockSubmitter(Submitter):
    def __init__(self) -> None:
        super().__init__()
        self.stock = 'canstockphoto'
        self.login_page = 'https://www.canstockphoto.ru/auth/login/'
        self.start_page = 'https://www.canstockphoto.ru/portfolio/unfinished/'
    
    def authenticate(self, auth_data: Tuple) -> None:
        ''' Fill in user/passwd and click button
        '''
        super().authenticate(auth_data)
        
        elem_uname = self.driver.find_element_by_name('username')
        elem_uname.send_keys(auth_data[0])
        elem_passwd = self.driver.find_element_by_name('password')
        elem_passwd.send_keys(auth_data[1])
        elem_button = self.driver.find_element_by_css_selector('button.btn.btn-block.btn-csp-orange')
        elem_button.click()
    
    def submit(self) -> None:
        ''' In the loop: remove invalid items, select all and press Submit button
        '''
        while True:
            self.delete_invalid()
            
            self.driver.get(self.start_page)
            elem_checkbox = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="accept"]')))
            elem_checkbox.click()
            
            elem_submit_btn = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.btn.btn-lg.btn-csp-orange.btn-submit')))
            if 'disabled' in elem_submit_btn.get_attribute('class'):
                break
            
            elem_submit_btn.click()
            self.check_captcha()
            
    
    def delete_invalid(self) -> None:
        ''' Remove invalid items by expanding info area and clicking Recycle button
        '''
        while True:
            self.driver.get(self.start_page)
            wrong_items = self.driver.find_elements_by_xpath('//*[@id="portfolio"]/table/tbody[@class="danger"]')
            if len(wrong_items) > 0:
                btn_edit = wrong_items[0].find_element_by_xpath('./tr[1]/td[5]/span')                    
                btn_edit.click()
            else:
                break

            btn_delete = WebDriverWait(wrong_items[0],10).until(EC.element_to_be_clickable((By.XPATH, './tr[2]/td/form/div[2]/div/span')))
            ActionChains(self.driver).move_to_element(btn_delete).click(btn_delete).perform()
                
            btn_confirm = WebDriverWait(self.driver,10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn-confirm')))                
            btn_confirm.click()
    
        
class DepositSubmitter(Submitter):
    def __init__(self) -> None:
        super().__init__()
        self.stock = 'depositphotos'
        self.login_page = ''
        self.start_page = ''
        
class DreamstimeSubmitter(Submitter):
    def __init__(self) -> None:
        super().__init__()
        self.stock = 'dreamstime'
        self.login_page = 'https://www.dreamstime.com/'
        self.start_page = ''
        
class One23Submitter(Submitter):
    def __init__(self) -> None:
        super().__init__()
        self.stock = '123rf'
        self.login_page = 'https://ru.123rf.com/login.php'
        self.start_page = 'https://ru.123rf.com/contributor/manage-content?tab=draft'

    def authenticate(self, auth_data: Tuple) -> None:
        ''' Fill in user/passwd and click button
        '''
        super().authenticate(auth_data)
        elem_uname = self.driver.find_element_by_name('userName')
        # elem_uname = driver.find_element_by_name('uid')
        elem_uname.send_keys(auth_data[0])

        # elem_passwd = driver.find_element_by_name('password')
        elem_passwd = self.driver.find_element_by_name('userPassword')
        elem_passwd.send_keys(auth_data[1])

        # elem_button = driver.find_element_by_css_selector('#panel_login_submit')
        elem_button = self.driver.find_element_by_name('login-button')
        elem_button.click()        
       
    def submit(self) -> None:
        ''' In the loop: remove invalid items, select all and press Submit button
        '''
        while True:
            self.driver.get(self.start_page)
            
            if self.check_unprocessed_left():
                self.delete_invalid()
            else:
                break
            
            if self.check_unprocessed_left():
                elem_submit_btn = WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#submit-draft-btn')))
                # elem_submit_btn = driver.find_element_by_css_selector('button#submit-draft-btn')
                elem_submit_btn.click()
                self.check_captcha()
            else:
                break            

    
    def delete_invalid(self) -> None:
        ''' Remove invalid items by selecting and clicking Recycle button
        '''
        while True:
            self.driver.get(self.start_page)
            #check_captcha?
            WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="manage-content-grid"]')))            
            all_items = self.driver.find_elements_by_xpath('//*[@id="manage-content-grid"]')            
            
            valid_items = self.driver.find_elements_by_xpath('//*[@id="green-details-complete"]')
            
            if len(all_items) - len(valid_items) > 0:
                for item in all_items:
                    invalid_itmes = item.find_elements_by_xpath('./div/label/div[1][@id="green-details-complete"]')
                    if len(invalid_itmes) == 0:
                        img = item.find_element_by_xpath('./div/label/div[1]/img')
                        img.click()
                bnt_delete = self.driver.find_element_by_xpath('//*[@id="delete-button"]')
                bnt_delete.click()
                modal_elems = self.driver.find_elements_by_xpath('//*[@id="delete-content-modal"]/div[2]/button[2]')
                if len(modal_elems) > 0:
                    modal_elems[0].click()
                break
            else:
                break
             
            if not self.check_unprocessed_left():
                break
    
    def check_unprocessed_left(self) -> bool:
        elem_select_all = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#select-all')))
        # driver.find_element_by_css_selector('#select-all')
        elem_select_all.click()
            
        selected_cnt_elem = self.driver.find_element_by_xpath('//*[@id="container-content-container-box"]/div/div[2]/div/div/div/div/div[1]/div[2]/div/span[1]/b')
        selected_cnt = selected_cnt_elem.text
        if int(selected_cnt) == 0:
            return False
        else:
            return True

        

def create_submitter(stock:str) -> Submitter:
    if stock == '123':
        submitter = One23Submitter()
    elif stock == 'cs':
        submitter = CanStockSubmitter()
    elif stock == 'dt':
        submitter = DreamstimeSubmitter()
    elif stock == 'dp':
        submitter = DepositSubmitter()
    else:
        submitter = None
    
    return submitter