/**
 * City data for investment calculator
 */

export interface CityData {
  name: string;
  province: string;
  province_code: string;
  region: string;
  peak_price: number;
  valley_price: number;
  flat_price: number;
  description: string;
}

export const cities: CityData[] = [
  {
    name: '深圳',
    province: '广东',
    province_code: 'GD',
    region: '华南',
    peak_price: 1.2,
    valley_price: 0.35,
    flat_price: 0.75,
    description: '一线城市，峰谷价差大，补贴政策好',
  },
  {
    name: '广州',
    province: '广东',
    province_code: 'GD',
    region: '华南',
    peak_price: 1.15,
    valley_price: 0.38,
    flat_price: 0.72,
    description: '省会城市，工业基础雄厚',
  },
  {
    name: '佛山',
    province: '广东',
    province_code: 'GD',
    region: '华南',
    peak_price: 1.15,
    valley_price: 0.38,
    flat_price: 0.72,
    description: '制造业基地，用电需求大',
  },
  {
    name: '东莞',
    province: '广东',
    province_code: 'GD',
    region: '华南',
    peak_price: 1.15,
    valley_price: 0.38,
    flat_price: 0.72,
    description: '电子产业集中，储能需求强',
  },
  {
    name: '杭州',
    province: '浙江',
    province_code: 'ZJ',
    region: '华东',
    peak_price: 1.1,
    valley_price: 0.4,
    flat_price: 0.7,
    description: '数字经济中心，政策支持力度大',
  },
];

export type ScenarioType = 'optimistic' | 'base' | 'conservative';

export const scenarios: {
  value: ScenarioType;
  name: string;
  description: string;
  color: string;
}[] = [
  {
    value: 'optimistic',
    name: '乐观情景',
    description: '假设峰谷价差扩大10%，补贴增加0.1元/kWh',
    color: 'bg-green-500',
  },
  {
    value: 'base',
    name: '基准情景',
    description: '基于当前电价政策的基准情景',
    color: 'bg-blue-500',
  },
  {
    value: 'conservative',
    name: '保守情景',
    description: '假设峰谷价差缩小10%，补贴减少0.05元/kWh',
    color: 'bg-orange-500',
  },
];
