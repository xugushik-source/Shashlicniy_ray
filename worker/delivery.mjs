import DELIVERY from '../config/delivery.json' with {type:'json'};
export function resolveDeliveryCity(id=DELIVERY.default_city_id){const city=DELIVERY.cities.find(city=>city.id===id);if(typeof id!=='string'||!city||city.active!==true)throw Error('CITY_UNAVAILABLE');return city}
export function deliverySettings(){const city=DELIVERY.cities.find(city=>city.id===DELIVERY.default_city_id);return {default_city_id:DELIVERY.default_city_id,cities:DELIVERY.cities,city:city?.names||{}}}
