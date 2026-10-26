#pragma once
#include <cstdint>
using esp_err_t=int;constexpr esp_err_t ESP_OK=0,ESP_ERR_INVALID_STATE=1;
struct esp_task_wdt_config_t {uint32_t timeout_ms,idle_core_mask;bool trigger_panic;};
inline esp_err_t esp_task_wdt_init(const esp_task_wdt_config_t*){return ESP_OK;}
inline esp_err_t esp_task_wdt_reconfigure(const esp_task_wdt_config_t*){return ESP_OK;}
inline esp_err_t esp_task_wdt_status(void*){return ESP_OK;}
inline esp_err_t esp_task_wdt_add(void*){return ESP_OK;}
inline esp_err_t esp_task_wdt_reset(){return ESP_OK;}
