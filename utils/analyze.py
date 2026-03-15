import json
import csv
import re
import pandas as pd
from typing import TypeAlias, Optional, final
from enum import auto, StrEnum
from .sentence import *
from .data_structure import *


class UnitStatus:
    def __init__(self, team='', **kwargs):
        self.team = team
        self.name = kwargs.get('name', '')
        self.country = kwargs.get('country', None)
        self.level = kwargs.get('level', None)
        self.n_red = kwargs.get('n_red', None)
        self.兵力最大值 = kwargs.get('initial_hp', None)
        self.兵力 = kwargs.get('initial_hp', None)
        self.supply = 100
        
        self.武力 = -1
        self.智力 = -1
        self.统率 = -1
        self.先攻 = -1
        self.effects = []
        self.skills = {}

def percent_to_float(s):
    if isinstance(s, str) and s.endswith('%'):
        try:
            return float(s.strip('%')) / 100
        except ValueError:
            return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
    
def get_df(log):
    attr_columns = []
    seen = set()
    for record in log:
        for k in record.keys():
            if k not in seen:
                attr_columns.append(k)
                seen.add(k)
    
    attr_filled = []
    for record in log:
        row = {col: record.get(col, 0) for col in attr_columns}
        attr_filled.append(row)
    df_log = pd.DataFrame(attr_filled, columns=attr_columns)
    return df_log

def analysis(report_id, config, data):
    idx = int(report_id.stem)
    report_save_path = report_id / "analysis_result.xlsx"
    
    general_dict = {}

    current_initiator = None  # 当前发动战法的武将
    current_skill = ''
    
    attr_change_log = []
    damage_log = []
    heal_log = []

    with_抵御 = False
    with_会心 = False
    
    for team_name, team_data in config.items():
        team_color = 'blue' if team_name == 'left' else 'red'
        print(f"Processing team: {team_color}")
        for idx, general_data in team_data.items():
            general_tag = f"{general_data[0]['name']}_{team_color}"
            general = UnitStatus(team_color, **general_data[0])
            for skill in general_data[1:]:
                general.skills[skill['skill_name']] = skill
            general_dict[general_tag] = general
    print(general_dict.keys())

    # 战报分析
    for round_id, items in data.items():
        for sentence in items:           
            tags = sentence.get_sentence()
            general_tag = f'{tags[0][0]}_{tags[0][1]}'

            sentence.print_line()
            # 获取当前补给值
            if isinstance(sentence, Supply):
                #print(f'{general_tag}队当前补给值为{tags[1][0]},造成伤害降低{tags[2][0]}%')
                pass
            elif isinstance(sentence, StartAction):
                #print(f'{general_tag}开始行动')
                pass
            elif isinstance(sentence, HealMagical):
                #print(f'{general_tag}触发攻心')
                pass
            elif isinstance(sentence, HealPhysical):
                #print(f'{general_tag}触发倒戈')
                pass
            elif isinstance(sentence, CannotFight):
                #print(f'{general_tag}兵力为0，无法再战')
                pass
            elif isinstance(sentence, DoubleAttack):
                #print(f'{general_tag}发动连击')
                pass
            elif isinstance(sentence, DoubleAttacking):
                #print(f'{general_tag}进行连击')
                pass
            elif isinstance(sentence, DodgeActivate):
                #print(f'{general_tag}发动闪避')
                pass
            elif isinstance(sentence, ApplyFormation):
                #print(f'{general_tag}队获得【阵型--{tags[1][0]}阵】强化效果')
                current_initiator = general_tag
                current_skill = f'{tags[1][0]}阵'
            elif isinstance(sentence, SkillGain):
                #print(f'{general_tag}获得战法【{tags[1][0]}】')
                pass
            elif isinstance(sentence, EffectRefresh):
                #print(f'{general_tag}的【{tags[1][0]}】效果已刷新')
                pass
            elif isinstance(sentence, BuildBuff):
                #print(f'{general_tag}队由于【{tags[1][0]}】的效果')
                pass
            elif isinstance(sentence, SkillActivate):
                #print(f'{general_tag}发动战法【{tags[1][0]}】')
                current_initiator = general_tag
                current_skill = tags[1][0]
            elif isinstance(sentence, EffectFromOther):
                #print(f'{general_tag}执行来自【{tags[1][0]}】的「{tags[2][0]}」效果')
                #TODO 查找是哪个武将的技能
                current_initiator = general_tag
                current_skill = tags[1][0]
            elif isinstance(sentence, SkillFromOther):
                #print(f'{general_tag}执行来自「{tags[1][0]}」效果')
                #TODO 查找是哪个武将的技能
                current_initiator = general_tag
                current_skill = tags[1][0]
            elif isinstance(sentence, EffectApply):
                #print(f'{general_tag}的【{tags[1][0]}】效果已施加')
                pass
            elif isinstance(sentence, EffectApplyFail):
                #print(f'{general_tag}的【{tags[1][0]}】效果已施加。{general_tag}持有清醒，效果暂时失效')
                pass
            elif isinstance(sentence, EffectExpire):
                #print(f'{general_tag}的【{tags[1][0]}】效果已消失')
                pass
            elif isinstance(sentence, EffectExecute):
                #print(f'{general_tag}执行【{tags[1][0]}】效果')
                current_initiator = general_tag
                current_skill = tags[1][0]
            elif isinstance(sentence, EffectNotExecute):
                #print(f'{general_tag}未触发【{tags[1][0]}】的「{tags[2][0]}」效果')
                pass
            elif isinstance(sentence, SkillNotExecute):
                #print(f'{general_tag}因几率未发动战法【{tags[1][0]}】')
                pass
            elif isinstance(sentence, NationEnhance):
                #print(f'{general_tag}队获得【{tags[1][0]}】强化效果，属性提升{tags[2][0]}%')
                current_initiator = general_tag
                current_skill = tags[1][0]
            elif isinstance(sentence, TroopEnhance):
                #print(f'{general_tag}队获得【{tags[1][0]}】强化效果')
                current_initiator = general_tag
                current_skill = tags[1][0]
            elif isinstance(sentence, Keep):
                #print(f'{general_tag}队的【{tags[1][0]}】保持不变{tags[2][0]}({tags[3][0]})')
                pass
            elif isinstance(sentence, CritPhysicalHit):
                #print(f'{general_tag}触发会心，会心伤害为{tags[1][0]}')
                current_initiator = general_tag
            elif isinstance(sentence, CritMagicalHit):
                #print(f'{general_tag}触发奇谋，奇谋伤害为{tags[1][0]}')
                current_initiator = general_tag
            elif isinstance(sentence, DamageIncrease):
                #print(f'{general_tag}伤害提升{tags[1][0]}')
                pass
            elif isinstance(sentence, DamageReduce):
                #print(f'{general_tag}伤害提升{tags[1][0]}')
                pass
            elif isinstance(sentence, EffectStacked):
                #print(f'{general_tag}的{tags[1][0]}效果已叠加{tags[2][0]}层')
                pass
            elif isinstance(sentence, EffectStackedFull):
                #print(f'{general_tag}的{tags[1][0]}效果已叠满{tags[2][0]}层')
                pass
            elif isinstance(sentence, EffectFull):
                #print(f'{general_tag}的{tags[1][0]}效果已满层{tags[2][0]}次')
                pass
            elif isinstance(sentence, DodgeSuccess):
                #print(f'{general_tag}成功闪避{tags[1][0]}的伤害')
                pass
            elif isinstance(sentence, NormalHit):
                #print(f'{general_tag}对{tags[1][0]}发动普通攻击')
                current_initiator = general_tag
                current_skill = '普通攻击'
            elif isinstance(sentence, EffectDueTo):
                #print(f'{general_tag}由于{tags[1][0]}【{tags[2][0]}】的「{tags[3][0]}」效果')
                #current_initiator = tags[1][0]
                
                current_initiator = f"{tags[1][0]}_{tags[1][1]}"
                current_skill = tags[2][0]
            elif isinstance(sentence, EffectFrom):
                #print(f'{general_tag}由于{tags[1][0]}「{tags[2][0]}」效果')
                #current_initiator = tags[1][0]
                current_initiator = f"{tags[1][0]}_{tags[1][1]}"
                current_skill = tags[2][0]
            elif isinstance(sentence, NormalHitFail):
                #print(f'{general_tag}由于{tags[1][0]}【{tags[2][0]}】的「{tags[3][0]}」效果[{tags[4][0]}]无法{tags[5][0]}')
                pass
            elif isinstance(sentence, StatusChange):
                #print(f'{general_tag}的【{tags[1][0]}】{tags[2][0]}{tags[3][0]}({tags[4][0]})')
                #print(tags)
                setattr(general_dict[general_tag], tags[1][0], tags[4][0])
                record = {}
                        
                record['回合'] = round_id
                record['目标武将'] = general_tag
                record['属性'] = tags[1][0]
                record['变化值'] = ('' if tags[2][0] == '提升' else '-') + tags[3][0]
                record['最终值'] = tags[4][0]
                if current_initiator is not None:
                    record['发动武将'] = current_initiator
                    record['发动技能'] = current_skill
                    record['发动武将武力'] = getattr(general_dict.get(current_initiator, None), '武力', -1)
                    record['发动武将智力'] = getattr(general_dict.get(current_initiator, None), '智力', -1)
                    record['发动武将统率'] = getattr(general_dict.get(current_initiator, None), '统率', -1)
                    record['发动武将先攻'] = getattr(general_dict.get(current_initiator, None), '先攻', -1)

                    whos_skill = None
                    skill_name = current_skill.split('-')[0]
                    #print(f"Current: {current_initiator}")
                    if skill_name in general_dict[current_initiator].skills.keys():
                        whos_skill = general_dict[current_initiator].skills[skill_name]
                    elif skill_name in general_dict[general_tag].skills.keys():
                        whos_skill = general_dict[general_tag].skills[skill_name]
                    
                    if whos_skill is not None:  
                        skill_level = whos_skill['skill_level']
                        skill_red = whos_skill['n_red']
                        record['技能等级'] = skill_level
                        record['技能红度'] = skill_red
                        #print(f"技能[{current_skill}]等级: {skill_level}, 红色: {skill_red}")
                        
                attr_change_log.append(record)
                #print(f"属性变化记录: {attr_change_log[-1]}")
                
            elif isinstance(sentence, Heal):
                #print(f'{general_tag}队恢复了兵力{tags[1][0]}({tags[2][0]})')

                other = 1 + percent_to_float(getattr(general_dict[current_initiator], '造成治疗效果', 0)) + percent_to_float(getattr(general_dict[general_tag], '受到治疗增加', 0))
                #clipped = percent_to_float(remove_parentheses(item[-1][0])) == general_dict[general_tag].兵力最大值 or percent_to_float(item[-2][0]) == 0

                #print(general_dict[general_tag].兵力最大值, percent_to_float(remove_parentheses(item[-1][0])), clipped)

                record = {}
                record['回合'] = round_id
                record['受影响武将'] = general_tag
                record['发动武将'] = current_initiator
                record['效果名称'] = current_skill
                record['治疗量'] = tags[-2][0]
                record['最终兵力'] = tags[-1][0]
                record['治疗率'] = 1.
                record['发动武将智力'] = general_dict[current_initiator].智力
                #record['发动武将兵力'] = general_dict[current_initiator].兵力
                record['治疗加成'] = other
                record['是否溢出'] = False
                
                whos_skill = None
                skill_name = current_skill.split('-')[0]
                if skill_name in general_dict[current_initiator].skills.keys():
                    whos_skill = general_dict[current_initiator].skills[skill_name]
                elif skill_name in general_dict[general_tag].skills.keys():
                    whos_skill = general_dict[general_tag].skills[skill_name]
                
                if whos_skill is not None:  
                    skill_level = whos_skill['skill_level']
                    skill_red = whos_skill['n_red']
                    record['技能等级'] = skill_level
                    record['技能红度'] = skill_red
                    #print(f"技能[{current_skill}]等级: {skill_level}, 红色: {skill_red}")
                    
                heal_log.append(record)
                setattr(general_dict[general_tag], '兵力', tags[-1][0])
                #print(f"兵力变化记录: {heal_log[-1]}")
                
            elif isinstance(sentence, SkillDamage):
                #print(f'{general_tag}由于{tags[1][0]}的【{tags[2][0]}】的伤害，损失了兵力{tags[3][0]}({tags[4][0]})')
                
                setattr(general_dict[general_tag], '兵力', tags[4][0])
                record = {}
                record['回合'] = round_id
                record['受影响武将'] = general_tag
                record['发动武将'] = f'{tags[1][0]}_{tags[1][1]}' 
                record['效果名称'] = tags[2][0]
                record['伤害量'] = tags[3][0]
                record['最终兵力'] = tags[4][0]
                record['发动武将武力'] = general_dict[current_initiator].武力
                record['受伤武将统率'] = general_dict[general_tag].统率
                record['发动武将兵力'] = general_dict[current_initiator].兵力
                damage_log.append(record)
                
            elif isinstance(sentence, SkillEffectDamage):
                #print(f'{general_tag}由于{tags[1][0]}【{tags[2][0]}】的「{tags[3][0]}」效果，损失了兵力{tags[4][0]}({tags[5][0]})')
                
                setattr(general_dict[general_tag], '兵力', tags[5][0])
                record = {}
                record['回合'] = round_id
                record['受影响武将'] = general_tag
                record['发动武将'] = f'{tags[1][0]}_{tags[1][1]}' 
                record['效果名称'] = tags[2][0]
                record['伤害量'] = tags[4][0]
                record['最终兵力'] = tags[5][0]
                record['发动武将武力'] = general_dict[current_initiator].武力
                record['受伤武将统率'] = general_dict[general_tag].统率
                record['发动武将兵力'] = general_dict[current_initiator].兵力
                damage_log.append(record)
                
            elif isinstance(sentence, EffectDamage):
                #print(f'{general_tag}由于{tags[1][0]}「{tags[2][0]}」效果，损失了兵力{tags[3][0]}({tags[4][0]})')
                
                setattr(general_dict[general_tag], '兵力', tags[4][0])
                record = {}
                record['回合'] = round_id
                record['受影响武将'] = general_tag
                record['发动武将'] = f'{tags[1][0]}_{tags[1][1]}' 
                record['效果名称'] = tags[2][0]
                record['伤害量'] = tags[3][0]
                record['最终兵力'] = tags[4][0]
                record['发动武将武力'] = general_dict[current_initiator].武力
                record['受伤武将统率'] = general_dict[general_tag].统率
                record['发动武将兵力'] = general_dict[current_initiator].兵力
                damage_log.append(record)
                
                
            elif isinstance(sentence, HPReduce):
                #print(f'{general_tag}损失了兵力{tags[1][0]}({tags[2][0]})')
                
                setattr(general_dict[general_tag], '兵力', tags[2][0])
                record = {}
                record['回合'] = round_id
                record['受影响武将'] = general_tag
                record['发动武将'] = current_initiator
                record['效果名称'] = '普通攻击'
                record['伤害量'] = tags[1][0]
                record['最终兵力'] = tags[2][0]
                record['发动武将武力'] = general_dict[current_initiator].武力
                record['受伤武将统率'] = general_dict[general_tag].统率
                record['发动武将兵力'] = general_dict[current_initiator].兵力
                damage_log.append(record)
                
            else:
                raise RuntimeError(f"无法识别该sentence: {sentence}")

            '''  
            # 治疗公式
            heal_amount = int(
                0.930094
                + 0.005533 * math.pow(self.soldiers, 0.27478)
                * actual_multiplier
                * (
                    0.002574 * math.pow(self.status.intelligence, 2)
                    + 0.055828 * self.status.intelligence
                    + 117.637582
                )
                * (1 + self.status.heal_bonus)
                * (1 + target.status.get_heal_bonus)
                )
            '''
            
    with pd.ExcelWriter(report_save_path) as writer:
        df_log = get_df(attr_change_log)
        df_log.to_excel(writer, sheet_name='attr_change', index=False)
        
        df_log = get_df(damage_log)
        df_log.to_excel(writer, sheet_name='damage', index=False)
        
        df_log = get_df(heal_log)
        df_log.to_excel(writer, sheet_name='heal', index=False)

if __name__ == "__main__":
    analysis()