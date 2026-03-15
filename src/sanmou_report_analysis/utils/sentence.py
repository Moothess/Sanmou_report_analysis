import re
import cv2
from .ocr import ocr_text
import numpy as np
from .data_structure import TextColor

class LineSentence:    
    def __init__(self, color_list):
        self.color_list = color_list
        self.sentence = []
        
    @staticmethod
    def match(color_list):
        return False
        
    def get_sentence(self):
        return self.sentence

    def print_line(self):
        return ''

def remove_brackets(text):
    return re.sub(r'[\(\)\（\）\[\]\【\】\{\}\｛\｝\<\>\!\《\》\「\」\『\』\!\！]', '', text)


def chinese_only(text):
    return re.sub(r'[^\u4e00-\u9fff]', '', text)

def extract_numbers(text):
    return re.sub(r'[^\d\.\%]', '', text)

def get_text_between(text, start_str, end_str):
    try:
        matched_str = re.search(f'{start_str}(.*?){end_str}', text).group(1).strip()
        matched_str = remove_brackets(matched_str)
        return matched_str
    except:
        print(f"无法从文本中提取指定内容: {text}，起始标志: {start_str}，结束标志: {end_str}。尝试删除标志后提取。")
        matched_str = text.replace(start_str, '')
        matched_str = matched_str.replace(end_str, '')
        matched_str = remove_brackets(matched_str)
        return matched_str

def calculate_similarity(ocr_text, in_str, not_in_str=''):
    score = 0
    for in_word in in_str:
        if in_word in ocr_text:
            score += 1
    
    for not_in_word in not_in_str:
        if not_in_word not in ocr_text:
            score += 1
    return score / (len(in_str) + len(not_in_str))

class Supply(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, TextColor.WHITE.value, TextColor.WHITE.value]
        patch_texts.append(self.color_list[0][0])
        numbers = re.findall(r'\d+', self.color_list[1][0])
        assert len(numbers) == 2, numbers
        patch_texts.append(numbers[0])
        patch_texts.append(numbers[1])
        #patch_texts.append(f'队当前补给值为{numbers[0]}，造成伤害降低{numbers[1]}%')
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '队当前补给值为造成伤害降低')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队当前补给值为{self.sentence[1][0]},造成伤害降低{self.sentence[2][0]}%')
    
class StartAction(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '开始行动')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}开始行动')

class HealMagical(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '触发攻心')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}触发攻心')
    
class HealPhysical(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '触发倒戈')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}触发倒戈')
    
class CannotFight(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '兵力为无法再战')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}兵力为0，无法再战')
    
class DoubleAttack(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '发动连击')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}发动连击')
    
class DoubleAttacking(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '进行连击')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}进行连击')
    
class DodgeActivate(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '抵御机会消耗伤害减少')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}发动闪避')
    
class ApplyFormation(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        patch_texts.append(self.color_list[0][0])
        
        idx = self.color_list[1][0].rfind('阵')
        formation_name = self.color_list[1][0][idx-2:idx] if idx >= 2 else ''
        patch_texts.append(formation_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '队获得阵型强化效果')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队获得【阵型--{self.sentence[1][0]}阵】强化效果')

class TypeEnhance(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_colors = [self.color_list[0][1].value]
        patch_texts = [self.color_list[0][0]]
        
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '队获得兵种进阶效果')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队获得兵种进阶效果')

class UpgradeEnhance(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_colors = [self.color_list[0][1].value]
        patch_texts = [self.color_list[0][0]]
        
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '队获得举荐的效果')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队获得【举荐】的效果')

class StatusChange(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, TextColor.WHITE.value, self.color_list[1][1].value, self.color_list[2][1].value, self.color_list[3][1].value, ]
        patch_texts.append(self.color_list[0][0])
        status_name = self.color_list[1][0]
        status_change = status_name
        tag = ''
        if status_change.startswith('的'):
            status_change = status_change[1:]
        if status_change.endswith('提升'):
            status_change = status_change[:-2]
            tag = '提升'
        elif status_change.endswith('降低'):
            status_change = status_change[:-2]
            tag = '降低'
        status_change = chinese_only(remove_brackets(status_change))
        patch_texts.append(status_change)
        patch_texts.append(tag)

        status_add = self.color_list[2][0]
        patch_texts.append(status_add)
        status_final = self.color_list[3][0]
        patch_texts.append(remove_brackets(status_final))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[2][1] != TextColor.YELLOW:
            return 0

        sim1 = calculate_similarity(color_list[1][0], '的提升')
        sim2 = calculate_similarity(color_list[1][0], '的降低')
        return max(sim1, sim2)
        #if ('提升' in color_list[1][0] or '降低' in color_list[1][0]): #and '的' in color_list[1][0]:
        #    return 1
        #else:
        #    return 0

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的【{self.sentence[1][0]}】{self.sentence[2][0]}{self.sentence[3][0]}({self.sentence[4][0]})')

class SkillGain(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_name = self.color_list[1][0].replace('获得战法', '').strip()
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '获得战法')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}获得战法【{self.sentence[1][0]}】')

class EffectRefresh(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '的', '效果')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '的效果已刷新')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的【{self.sentence[1][0]}】效果已刷新')

class BuildBuff(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '由于', '的效果')
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '队由于的效果')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队由于【{self.sentence[1][0]}】的效果')

class SkillActivate(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        patch_texts.append(self.color_list[0][0])
        skill_name = self.color_list[1][0].replace('发动战法', '').strip()
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '发动战法', '未')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}发动战法【{self.sentence[1][0]}】')

class EffectFromOther(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, TextColor.WHITE.value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)

        skill_str = self.color_list[1][0]
        #skill_name = re.search(r'执行来自(.*?)的', skill_str).group(1).strip()
        skill_name = get_text_between(skill_str, '执行来自', '的')
        patch_texts.append(skill_name)

        effect_name = get_text_between(skill_str, '的', '效果')
        patch_texts.append(effect_name)

        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '执行来自的效果')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}执行来自【{self.sentence[1][0]}】的「{self.sentence[2][0]}」效果')

class SkillFromOther(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)

        skill_name = get_text_between(self.color_list[1][0], '执行来自', '效果')
        patch_texts.append(skill_name)

        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '执行来自效果', '的')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}执行来自「{self.sentence[1][0]}」效果')

class EffectApply(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '的', '效果已施加')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '的效果已施加')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的【{self.sentence[1][0]}】效果已施加')

class EffectApplyFail(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        effect_name = self.color_list[1][0]
        skill_name = get_text_between(effect_name, '的', '效果已施加')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[2][1] not in [TextColor.BLUE, TextColor.RED]:
            return 0

        sim1 = calculate_similarity(color_list[1][0], '的效果已施加', '')
        sim2 = calculate_similarity(color_list[3][0], '持有效果暂时失效', '')
        return (sim1 + sim2) / 2
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的【{self.sentence[1][0]}】效果已施加。{general_tag}持有清醒，效果暂时失效')

class EffectExpire(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_name = get_text_between(self.color_list[1][0], '的', '效果已消失')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '的效果已消失')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的【{self.sentence[1][0]}】效果已消失')

class EffectExecute(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        #skill_name = re.search(r'执行(.*?)效果', skill_str).group(1).strip()
        skill_name = get_text_between(skill_str, '执行', '效果')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '执行效果', '来自')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}执行【{self.sentence[1][0]}】效果')

class EffectNotExecute(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[1][1].value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '未触发', '的')
        patch_texts.append(skill_name)
        skill_name = get_text_between(skill_str, '的', '效果')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '未触发的效果')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}未触发【{self.sentence[1][0]}】的「{self.sentence[2][0]}」效果')

class SkillNotExecute(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[1][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        idx = skill_str.find('发动战法')
        skill_name = skill_str[idx+4:]
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '因几率未发动战法')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}因几率未发动战法【{self.sentence[1][0]}】')

class NationEnhance(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, TextColor.WHITE.value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        nation_name = get_text_between(skill_str, '队获得', '强化效果')
        patch_texts.append(nation_name)
        
        numbers = re.findall(r'\d+', skill_str)
        patch_texts.append(numbers[0])
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '队获得强化效果属性提升')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队获得【{self.sentence[1][0]}】强化效果，属性提升{self.sentence[2][0]}%')

class TroopEnhance(LineSentence):
    len_patch = 2
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '队获得', '强化效果')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '强化效果', '属性阵型')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队获得【{self.sentence[1][0]}】强化效果')

class Heal(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        #skill_name = self.color_list[1][0]
        #patch_texts.append(skill_name)
        skill_name = self.color_list[2][0]
        patch_texts.append(skill_name)
        skill_name = self.color_list[3][0]
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        if color_list[2][1] == TextColor.GREEN:
            return 1
        else:
            return 0

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队恢复了兵力{self.sentence[1][0]}({self.sentence[2][0]})')

class Keep(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [color.value for _, color in self.color_list]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '的', '保持不变')
        patch_texts.append(skill_name)
        skill_name = self.color_list[2][0]
        patch_texts.append(skill_name)
        skill_name = self.color_list[3][0]
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[2][1] != TextColor.YELLOW:
            return 0

        return calculate_similarity(color_list[1][0], '队的保持不变')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}队的【{self.sentence[1][0]}】保持不变{self.sentence[2][0]}({self.sentence[3][0]})')

class CritPhysicalHit(LineSentence):
    len_patch = 3
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[2][0]
        patch_texts.append(skill_str)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '触发会心伤害为')
        
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}触发会心，会心伤害为{self.sentence[1][0]}')

class CritMagicalHit(LineSentence):
    len_patch = 3
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[2][0]
        patch_texts.append(skill_str)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '触发奇谋伤害为')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}触发奇谋，奇谋伤害为{self.sentence[1][0]}')

class DamageIncrease(LineSentence):
    len_patch = 3
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[2][0]
        patch_texts.append(remove_brackets(skill_str))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '伤害提升')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}伤害提升{self.sentence[1][0]}')

class DamageReduce(LineSentence):
    len_patch = 3
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[2][0]
        patch_texts.append(remove_brackets(skill_str))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[2][1] != TextColor.YELLOW:
            return 0

        return calculate_similarity(color_list[1][0], '伤害降低')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}伤害降低{self.sentence[1][0]}')

class SkillDamage(LineSentence):
    len_patch = 6
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, TextColor.WHITE.value, self.color_list[4][1].value, self.color_list[5][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        skill_str = self.color_list[3][0]
        skill_name = get_text_between(skill_str, '的', '的伤害')
        patch_texts.append(skill_name)
        damage = self.color_list[4][0]
        patch_texts.append(damage)
        hp = self.color_list[5][0]
        patch_texts.append(extract_numbers(hp))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[3][0].count('的') < 2:
            return 0
        
        return calculate_similarity(color_list[3][0], '的伤害损失了兵力')
        #if color_list[3][0].count('的') >= 2:
        #    return 1
        #else:
        #    return 0
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}由于{self.sentence[1][0]}的【{self.sentence[2][0]}】的伤害，损失了兵力{self.sentence[3][0]}({self.sentence[4][0]})')

class SkillEffectDamage(LineSentence):
    len_patch = 6
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, TextColor.WHITE.value, TextColor.WHITE.value, self.color_list[4][1].value, self.color_list[5][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        skill_str = self.color_list[3][0]
        idx = skill_str.find('的')
        skill_name = skill_str[:idx] if idx != -1 else ''
        patch_texts.append(remove_brackets(skill_name))
        skill_name = get_text_between(skill_str, '的', '效果')
        patch_texts.append(skill_name)
        damage = self.color_list[4][0]
        patch_texts.append(damage)
        hp = self.color_list[5][0]
        patch_texts.append(extract_numbers(hp))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return (calculate_similarity(color_list[3][0], '的效果损失了兵力') + calculate_similarity(color_list[5][0], '', '无法')) / 2.
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}由于{self.sentence[1][0]}【{self.sentence[2][0]}】的「{self.sentence[3][0]}」效果，损失了兵力{self.sentence[4][0]}({self.sentence[5][0]})')

class EffectDamage(LineSentence):
    len_patch = 6
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, TextColor.WHITE.value, self.color_list[4][1].value, self.color_list[5][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        skill_str = self.color_list[3][0]
        idx = skill_str.find('效果')
        skill_name = skill_str[:idx] if idx != -1 else ''
        patch_texts.append(remove_brackets(skill_name))
        damage = self.color_list[4][0]
        patch_texts.append(damage)
        hp = self.color_list[5][0]
        patch_texts.append(extract_numbers(hp))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[3][0], '效果损失了兵力', '的') 

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}由于{self.sentence[1][0]}「{self.sentence[2][0]}」效果，损失了兵力{self.sentence[3][0]}({self.sentence[4][0]})')

class EffectStacked(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[1][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        if '己' in skill_str:
            skill_name = get_text_between(skill_str, '的', '己')
        else:
            skill_name = get_text_between(skill_str, '的', '已')
        patch_texts.append(skill_name)
        stacked = self.color_list[2][0]
        patch_texts.append(stacked)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        if color_list[2][1] != TextColor.YELLOW:
            return 0

        return calculate_similarity(color_list[1][0], '的已叠加')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的{self.sentence[1][0]}已叠加{self.sentence[2][0]}层')

class EffectStackedFull(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[1][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '的', '已叠满')
        patch_texts.append(skill_name)
        stacked = self.color_list[2][0]
        patch_texts.append(stacked)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        if color_list[2][1] != TextColor.YELLOW:
            return 0

        return calculate_similarity(color_list[1][0], '的效果已叠满')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的{self.sentence[1][0]}效果已叠满{self.sentence[2][0]}层')

class EffectFull(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[1][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        skill_str = self.color_list[1][0]
        skill_name = get_text_between(skill_str, '的', '已满层')
        patch_texts.append(skill_name)
        stacked = self.color_list[2][0]
        patch_texts.append(stacked)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        if color_list[2][1] != TextColor.YELLOW:
            return 0

        return calculate_similarity(color_list[1][0], '的已满层')
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}的{self.sentence[1][0]}效果已满层{self.sentence[2][0]}次')

class DodgeSuccess(LineSentence):
    len_patch = 3
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        #idx = hero_name2.find('的伤害')
        #hero_name2 = hero_name2[:idx] if idx != -1 else ''
        patch_texts.append(hero_name2)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        return calculate_similarity(color_list[1][0], '成功闪避')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}成功闪避{self.sentence[1][0]}的伤害')

class NormalHit(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[2][1] not in [TextColor.BLUE, TextColor.RED]:
            return 0

        return calculate_similarity(color_list[3][0], '发动普通攻击')

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}对{self.sentence[1][0]}发动普通攻击')

class NormalHitFail(LineSentence):
    len_patch = 6
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, TextColor.WHITE.value, TextColor.WHITE.value, self.color_list[2][1].value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        skill_str = self.color_list[3][0]
        idx = skill_str.find('的')
        skill_name = skill_str[:idx] if idx != -1 else ''
        patch_texts.append(remove_brackets(skill_name))
        skill_name = get_text_between(skill_str, '的', '效果')
        patch_texts.append(skill_name)
        hero_name3 = self.color_list[4][0]
        patch_texts.append(hero_name3)
        skill_str = self.color_list[5][0]
        skill_str = skill_str.replace('无法', '')
        patch_texts.append(skill_str)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        return (calculate_similarity(color_list[3][0], '的效果') + calculate_similarity(color_list[5][0], '无法进行')) / 2.

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}由于{self.sentence[1][0]}【{self.sentence[2][0]}】的「{self.sentence[3][0]}」效果[{self.sentence[4][0]}]无法进行{self.sentence[5][0]}')

class EffectDueTo(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, TextColor.WHITE.value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        skill_str = self.color_list[3][0]
        idx = skill_str.find('的')
        if idx != -1:
            skill_name = skill_str[:]
        else:
            idx = skill_str.find('效果')
            skill_name = skill_str[:idx]
        patch_texts.append(remove_brackets(skill_name))
        skill_name = get_text_between(skill_str, '的', '效果')
        patch_texts.append(skill_name)
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        if color_list[2][1] not in [TextColor.BLUE, TextColor.RED]:
            return 0

        return calculate_similarity(color_list[3][0], '的效果') 
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}由于{self.sentence[1][0]}【{self.sentence[2][0]}】的「{self.sentence[3][0]}」效果')

class EffectFrom(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, TextColor.WHITE.value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        hero_name2 = self.color_list[2][0]
        patch_texts.append(hero_name2)
        skill_str = self.color_list[3][0]
        idx = skill_str.find('效果')
        skill_name = skill_str[:idx]
        patch_texts.append(remove_brackets(skill_name))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]
        
    @staticmethod
    def match(color_list):
        if color_list[2][1] not in [TextColor.BLUE, TextColor.RED]:
            return 0

        return calculate_similarity(color_list[3][0], '效果', '的') 
    
    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}由于{self.sentence[1][0]}「{self.sentence[2][0]}」效果')

class HPReduce(LineSentence):
    len_patch = 4
    
    def __init__(self, color_list):
        super().__init__(color_list)
        patch_texts = []
        patch_colors = [self.color_list[0][1].value, self.color_list[2][1].value, self.color_list[3][1].value]
        hero_name = self.color_list[0][0]
        patch_texts.append(hero_name)
        damage = self.color_list[2][0]
        patch_texts.append(damage)
        hp = self.color_list[3][0]
        patch_texts.append(remove_brackets(hp))
        self.sentence = [[text, color] for text, color in zip(patch_texts, patch_colors)]

    @staticmethod
    def match(color_list):
        if color_list[2][1] in [TextColor.MAROON, TextColor.ORANGE]:
            return 1
        else:
            return 0

    def print_line(self):
        general_tag = f'{self.sentence[0][0]}_{self.sentence[0][1]}'
        print(f'{general_tag}损失了兵力{self.sentence[1][0]}({self.sentence[2][0]})')
