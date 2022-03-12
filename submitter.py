import click
import keyring
import json
import logging

from typing import List, Tuple
from selenium import webdriver
from time import sleep
from re import findall
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import UnexpectedAlertPresentException


class Submitter():
    def __init__(self) -> None:
        self.log = logging.getLogger('log')
        self.log.setLevel(logging.INFO)
        file_handler = logging.FileHandler(f'logs/tss.log')
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:: %(message)s')
        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)
        self.log.info('==========START==========')
    
    def run(self) -> None:
        try:
            self.driver = webdriver.Chrome()
            auth_data = self.get_auth_data()
            self.authenticate(auth_data=auth_data) 
            if self.check_captcha():
                self.submit()
            self.driver.close()
            click.echo('done')
              
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
        
    def check_captcha(self) -> bool:
        return True
        # if self._check_captcha_rc():
        #     print('\a') # beep
        #     confirm = click.prompt('Captcha detected. Already solved it? Y/N')
        #     if confirm == 'Y':
        #         return True
        #     else:
        #         return False
            
    def _check_captcha_rc(self) -> bool:
        iframes = self.driver.find_elements_by_xpath('/html/body/div[2]/div[2]/iframe')
        if len(iframes) > 0:
            title = iframes[0].get_attribute('title')
            print(title)
            if 'recaptcha' in title:
                return True
        
        return False


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
        self.login_page = 'https://depositphotos.com/login.html'
        self.start_page = 'https://depositphotos.com/files/unfinished.html'
    
    def authenticate(self, auth_data: Tuple) -> None:
        super().authenticate(auth_data)
        # btn_select_email = self.driver.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div[2]/div[3]/div[3]/div')
        btn_select_email = WebDriverWait(self.driver,15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/main/div/div/div[2]/div[3]/div[3]/div')))
        btn_select_email.click()
        
        elem_uname = self.driver.find_element_by_name('username')
        elem_uname.send_keys(auth_data[0])
        
        elem_passwd = self.driver.find_element_by_name('password')
        elem_passwd.send_keys(auth_data[1]) 
        
        btn_log_in = self.driver.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div[2]/div[2]/form/button')
        btn_log_in.click()    
        WebDriverWait(self.driver,15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/main/div/div/div[1]/div[1]/div/div[1]/div[1]/a')))
             
        
    def submit(self) -> None:
        while True:
            try:
                self.driver.get(self.start_page)

                elem_select_all = WebDriverWait(self.driver,15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="unfinished-editor"]/div/div/div[3]/div[1]/div/table/tbody/tr/th[1]/label/i')))
                    
                elem_select_all.click()
                    
                elem_qty_selected = self.driver.find_element_by_xpath('//*[@id="unfinished-editor"]/div/div/div[2]/div/span/span[1]')
                qty_selected = elem_qty_selected.text
                if qty_selected and int(qty_selected) > 0:
                    btn_submit = self.driver.find_element_by_xpath('//*[@id="unfinished-editor"]/div/div/div[2]/div/button[1]')
                    btn_submit.click()
                    self.waitUntilProcessed()
                    
                    # check invalid items
                    if self.check_invalid():
                        self.delete_invalid()
                else:
                    break

            except UnexpectedAlertPresentException as e:
                print(f'Exception catched:', e)
                self.driver.switch_to.alert.accept()
            


    
    def check_invalid(self) -> bool:
        # If some of the items remains selected after submit - they are invalid
        WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="unfinished-editor"]/div/div/div[2]/div/button[1]')))
        elem_qty_selected = self.driver.find_element_by_xpath('//*[@id="unfinished-editor"]/div/div/div[2]/div/span/span[1]')
        qty_selected = elem_qty_selected.text
        if qty_selected:
            return int(qty_selected) > 0
        else:
            return False
        
    def delete_invalid(self) -> None:
        btn_delete = self.driver.find_element_by_xpath('//*[@id="unfinished-editor"]/div/div/div[2]/div/div[2]/i[1]')
        btn_delete.click()
        self.waitUntilProcessed()
    
    def waitUntilProcessed(self) -> None:
        while True:
            elem_qty_selected = self.driver.find_element_by_xpath('//*[@id="unfinished-editor"]/div/div/div[2]/div/span/span[1]')
            text_amnt_selected = elem_qty_selected.text
            elem_qty_all = self.driver.find_element_by_xpath('//*[@id="unfinished-editor"]/div/div/div[2]/div/span/span[2]')
            text_amnt_all = elem_qty_all.text
            if not text_amnt_selected or text_amnt_selected != text_amnt_all:
                break
            else:
                sleep(1)    
        
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
            selected_items_xpath = '//*[@id="container-content-container-box"]/div/div[2]/div/div/div/div/div[1]/div[2]/div/span[1]'
            WebDriverWait(self.driver,15).until(EC.text_to_be_present_in_element((By.XPATH, selected_items_xpath), '0'))
                        
            if self.check_unprocessed_left():
                self.delete_invalid()
            else:
                break
            
            if self.check_unprocessed_left():
                WebDriverWait(self.driver,15).until(EC.text_to_be_present_in_element((By.XPATH, selected_items_xpath), '0'))
                elem_select_all = WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#select-all')))
                elem_select_all.click()
                # elem_submit_btn = WebDriverWait(self.driver,15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button#submit-draft-btn')))
                # elem_submit_btn = WebDriverWait(self.driver,15).until(EC.element_to_be_clickable( (By.CSS_SELECTOR, 'button#submit-draft-btn')))
                
                elem_submit_btn = self.driver.find_element_by_css_selector('button#submit-draft-btn')
                ActionChains(self.driver).move_to_element(elem_submit_btn).click(elem_submit_btn).perform()
                
                # elem_submit_btn = driver.find_element_by_css_selector('button#submit-draft-btn')
                elem_submit_btn.click()
                self.check_captcha()
            else:
                break            

    
    def delete_invalid(self) -> None:
        ''' Remove invalid items by selecting and clicking Recycle button
        '''
        while True:
            # self.driver.get(self.start_page)
            #check_captcha?
            WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="manage-content-grid"]')))            
            all_items = self.driver.find_elements_by_xpath('//*[@id="manage-content-grid"]')            
            
            valid_items = self.driver.find_elements_by_xpath('//*[@id="green-details-complete"]')
            
            if len(all_items) - len(valid_items) > 0:
                for item in all_items:
                    invalid_itmes = item.find_elements_by_xpath('./div/label/div[1][@id="green-details-complete"]')
                    if len(invalid_itmes) == 0:
                        img = item.find_element_by_xpath('./div/label/div[1]/img')
                        ActionChains(self.driver).move_to_element(img).click(img).perform()
                        # img.click()
                btn_delete = self.driver.find_element_by_xpath('//*[@id="delete-button"]')
                ActionChains(self.driver).move_to_element(btn_delete).click(btn_delete).perform()
                # bnt_delete.click()
                modal_elems = self.driver.find_elements_by_xpath('//*[@id="delete-content-modal"]/div[2]/button[2]')
                if len(modal_elems) > 0:
                    modal_elems[0].click()
                break
            else:
                break
             
    
    def check_unprocessed_left(self) -> bool:
        WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container-content-container-box"]/div/div[2]')))            
        items = self.driver.find_elements_by_xpath('//*[@id="manage-content-grid"]')
        return len(items) > 0


class Pond5Submitter(Submitter):
    def __init__(self) -> None:
        super().__init__()
        self.stock = 'pond5'
        self.login_page = 'https://www.pond5.com/'
        self.start_page = 'https://www.pond5.com/index.php?page=my_uploads'
    
    def authenticate(self, auth_data: Tuple) -> None:
        super().authenticate(auth_data) # /html/body/header/div/div[4]/div[4]/span  
        link_log_in = self.driver.find_element_by_xpath('/html/body/header/div/div[4]/div[4]/span')
        # link_log_in = self.driver.find_element_by_xpath('//*[@id="main"]/div[2]/div[2]/div/nav/div[1]/div[8]/a/span')
        link_log_in.click()
        
        elem_uname = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.ID, 'inputLoginModalLogin')))            
        # elem_uname = self.driver.find_element_by_id('inputLoginModalLogin')
        elem_uname.send_keys(auth_data[0])
        
        elem_passwd = self.driver.find_element_by_id('inputLoginModalPassword')
        elem_passwd.send_keys(auth_data[1])
        
        elem_button = self.driver.find_element_by_xpath('//*[@id="loginSignupLightbox"]/div/div[3]/div/div[2]/button')
        elem_button.click()
        
        elem_ava_xpath = '/html/body/header/div/div[4]/div[5]/div[1]/a/img'
        # WebDriverWait(self.driver,15).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/div[2]/div/nav/div[1]/div[8]/div[1]/a/img')))
        WebDriverWait(self.driver,15).until(EC.presence_of_all_elements_located((By.XPATH, elem_ava_xpath)))


    def submit(self) -> None:
        self.driver.get(self.start_page)
        btn_submit_xpath = '//*[@id="main"]/div/div[3]/form/div[10]/input'

        while True:
            if len( self.driver.find_elements_by_xpath(btn_submit_xpath)) == 0:
                break
            
            # //*[@id="main"]/div/div[3]/form/div[9]/input
            # main > div > div:nth-child(3) > form > div:nth-child(11) > input
            # main > div > div:nth-child(3) > form > div:nth-child(12) > input            
            
            cb_select_all = WebDriverWait(self.driver,15).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main"]/div/div[3]/form/div[1]/div/label')))
            self.check_invalid()
            
            header_area = self.driver.find_element_by_xpath('//*[@id="main"]/div/div[1]/div/div[1]/div[2]')

            ActionChains(self.driver).move_to_element(header_area).move_to_element(cb_select_all).click(cb_select_all).perform()
            # cb_select_all.click()
            
            btn_submit = WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((By.XPATH,btn_submit_xpath)))
            ActionChains(self.driver).move_to_element(btn_submit).click(btn_submit).perform()
 
    def check_invalid(self) -> None:
        sel_area = self.driver.find_element_by_css_selector('#main > div > div:nth-child(3)')
        errors_text_lst = findall(r'Error: .* Clip ID: \d*', sel_area.text)
        for error_text_line in errors_text_lst:
            error_ids = findall(r'Clip ID: (\d*)', error_text_line)
            if len(error_ids) > 0:
                self.delete_invalid(error_ids)
    
    def delete_invalid(self, error_ids: List[str]) -> None:
        header_area = self.driver.find_element_by_xpath('//*[@id="main"]/div/div[1]/div/div[1]/div[2]')
        for id in error_ids:
            btn_bin_xpath = f"//a[@class='p5_delete_item_btn u-isActionable' and @data-item-id='{id}']/div"
            wrong_items = self.driver.find_elements_by_partial_link_text(id)
            if len(wrong_items) > 0:
                btn_bin = WebDriverWait(self.driver,10).until(EC.presence_of_element_located((By.XPATH, btn_bin_xpath)))
                
                ActionChains(self.driver).move_to_element(header_area).move_to_element(btn_bin).perform()
                WebDriverWait(self.driver,15).until(EC.element_to_be_clickable((By.XPATH, btn_bin_xpath)))
                btn_bin.click()
                
                ActionChains(self.driver).move_to_element(btn_bin).click(btn_bin).perform()
                
                btn_delete = WebDriverWait(self.driver,20).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[13]/div[3]/div/button[2]/span[text()='Delete']"))) 
                ActionChains(self.driver).move_to_element(btn_delete).click(btn_delete).perform()
                
                # Wait until it disapears
                WebDriverWait(self.driver,10).until((EC.invisibility_of_element(btn_bin)))

    
def create_submitter(stock:str) -> Submitter:
    if stock == '123':
        submitter = One23Submitter()
    elif stock == 'cs':
        submitter = CanStockSubmitter()
    # elif stock == 'dt':
    #     submitter = DreamstimeSubmitter()
    elif stock == 'dp':
        submitter = DepositSubmitter()
    elif stock == 'p5':
        submitter = Pond5Submitter()
    else:
        submitter = None
    
    return submitter