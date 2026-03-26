/**
 * Step 1: Select City
 */

'use client';

import { CityData, cities } from '@/lib/investment/cities';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface SelectCityStepProps {
  selectedCity: CityData | null;
  onCitySelect: (city: CityData) => void;
}

export function SelectCityStep({ selectedCity, onCitySelect }: SelectCityStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium mb-2">选择投资城市</h3>
        <p className="text-sm text-muted-foreground">
          不同城市的峰谷电价和补贴政策不同，会影响投资回报
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cities.map((city) => {
          const isSelected = selectedCity?.name === city.name;

          return (
            <Card
              key={city.name}
              className={cn(
                'cursor-pointer transition-all hover:shadow-md',
                isSelected && 'ring-2 ring-primary'
              )}
              onClick={() => onCitySelect(city)}
            >
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">{city.name}</h4>
                    {isSelected && (
                      <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                        已选择
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{city.province}</p>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>峰时:</span>
                      <span className="font-medium">{city.peak_price}元</span>
                    </div>
                    <div className="flex justify-between">
                      <span>谷时:</span>
                      <span className="font-medium">{city.valley_price}元</span>
                    </div>
                    <div className="flex justify-between">
                      <span>价差:</span>
                      <span className="font-medium text-primary">
                        {(city.peak_price - city.valley_price).toFixed(2)}元
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    {city.description}
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {selectedCity && (
        <div className="p-4 bg-muted rounded-md">
          <p className="text-sm font-medium">已选择: {selectedCity.name}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {selectedCity.description}
          </p>
        </div>
      )}
    </div>
  );
}
