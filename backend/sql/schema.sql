-- 网页端药物检测系统数据库表结构
-- 与 docs/database_design.md 保持一致
-- 字符集统一使用 utf8mb4，支持中文与特殊符号

CREATE DATABASE IF NOT EXISTS drug_check
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE drug_check;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------
-- 1. 用户表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(64) NOT NULL UNIQUE COMMENT '登录账号',
    password_hash   VARCHAR(255) NOT NULL COMMENT '密码哈希（bcrypt）',
    real_name       VARCHAR(64) COMMENT '真实姓名',
    role            ENUM('admin','operator') DEFAULT 'operator' COMMENT '角色',
    status          TINYINT DEFAULT 1 COMMENT '0-禁用，1-启用',
    last_login_at   DATETIME,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- -----------------------------------------------------
-- 2. 药物类别表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS drug_categories (
    id                  INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    code                VARCHAR(32) NOT NULL UNIQUE COMMENT '类别编码 1-8',
    name                VARCHAR(64) NOT NULL COMMENT '类别名称',
    reference_drug_id   INT UNSIGNED COMMENT '默认参照物 id',
    wavelengths         JSON COMMENT '该类检测波长列表',
    denominator_index   INT DEFAULT 1 COMMENT '峰面积比值分母波长在 wavelengths 中的索引（默认第 2 个）',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药物类别表';

-- -----------------------------------------------------
-- 3. 对照品标准药物表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS reference_drugs (
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    category_id     INT UNSIGNED NOT NULL COMMENT '所属类别',
    name            VARCHAR(128) NOT NULL COMMENT '药物中文名',
    name_en         VARCHAR(128) COMMENT '药物英文名',
    cas_no          VARCHAR(64) COMMENT 'CAS 号',
    is_reference    TINYINT DEFAULT 0 COMMENT '是否为参照物 0/1',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_category_drug (category_id, name),
    CONSTRAINT fk_ref_cat FOREIGN KEY (category_id) REFERENCES drug_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对照品标准药物表';

-- -----------------------------------------------------
-- 4. 相对保留时间模型参数表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS rrt_model_params (
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    drug_id         INT UNSIGNED NOT NULL,
    sample_count    INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '训练样本数 N',
    mean            DOUBLE NOT NULL COMMENT '数学期望 μ',
    variance        DOUBLE NOT NULL COMMENT '方差 σ²',
    std_dev         DOUBLE NOT NULL COMMENT '标准差 σ',
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rrt_drug (drug_id),
    CONSTRAINT fk_rrt_drug FOREIGN KEY (drug_id) REFERENCES reference_drugs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='相对保留时间模型参数';

-- -----------------------------------------------------
-- 5. 峰面积比值模型参数表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS peak_area_model_params (
    id                  INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    drug_id             INT UNSIGNED NOT NULL,
    sample_count        INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '训练样本数 N',
    wavelengths         JSON COMMENT '波长列表',
    mean_vector         JSON COMMENT '期望向量 μ',
    covariance_matrix   JSON COMMENT '协方差矩阵 Σ',
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_area_drug (drug_id),
    CONSTRAINT fk_area_drug FOREIGN KEY (drug_id) REFERENCES reference_drugs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='峰面积比值模型参数';

-- -----------------------------------------------------
-- 6. 紫外吸收光谱模型参数表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS uv_spectrum_model_params (
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    drug_id         INT UNSIGNED NOT NULL,
    sample_count    INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '训练样本数 N',
    peak_count      INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '色谱峰个数',
    lambda_max_1    DOUBLE COMMENT '最大吸收波长 1',
    lambda_max_2    DOUBLE COMMENT '最大吸收波长 2',
    absorption_data JSON COMMENT '吸收/峰面积数据 {A245,A250,R1,A255,R2,A260,R3}',
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_uv_drug (drug_id),
    CONSTRAINT fk_uv_drug FOREIGN KEY (drug_id) REFERENCES reference_drugs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='紫外吸收光谱模型参数';

-- -----------------------------------------------------
-- 7. 原始实验记录表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_experiments (
    id                      INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    experiment_no           VARCHAR(64) NOT NULL UNIQUE COMMENT '实验编号（文件名）',
    category_id             INT UNSIGNED NOT NULL,
    reference_drug_id       INT UNSIGNED COMMENT '选用的参照物',
    reference_retention_time DOUBLE COMMENT '参照物保留时间 ts',
    operator_id             INT UNSIGNED,
    sample_location         VARCHAR(128) COMMENT '采样地点',
    file_name               VARCHAR(255) COMMENT '原始文件名',
    file_path               VARCHAR(512) COMMENT '原始文件路径',
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_exp_category (category_id),
    CONSTRAINT fk_exp_category FOREIGN KEY (category_id) REFERENCES drug_categories(id),
    CONSTRAINT fk_exp_ref_drug FOREIGN KEY (reference_drug_id) REFERENCES reference_drugs(id) ON DELETE SET NULL,
    CONSTRAINT fk_exp_operator FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原始实验记录';

-- -----------------------------------------------------
-- 8. 原始保留时间数据表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_retention_times (
    id                      INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    experiment_id           INT UNSIGNED NOT NULL,
    peak_index              INT UNSIGNED NOT NULL COMMENT '峰序号',
    retention_time          DOUBLE COMMENT '保留时间 tx',
    relative_retention_time DOUBLE COMMENT '相对保留时间 tx/ts',
    INDEX idx_exp_peak (experiment_id, peak_index),
    CONSTRAINT fk_raw_rt_exp FOREIGN KEY (experiment_id) REFERENCES raw_experiments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原始保留时间数据';

-- -----------------------------------------------------
-- 9. 原始峰面积数据表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_peak_areas (
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    experiment_id   INT UNSIGNED NOT NULL,
    peak_index      INT UNSIGNED NOT NULL COMMENT '峰序号',
    wavelength      INT UNSIGNED NOT NULL COMMENT '波长 nm',
    area            DOUBLE NOT NULL COMMENT '峰面积',
    INDEX idx_exp_peak_wl (experiment_id, peak_index, wavelength),
    CONSTRAINT fk_raw_area_exp FOREIGN KEY (experiment_id) REFERENCES raw_experiments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原始峰面积数据';

-- -----------------------------------------------------
-- 10. 原始紫外吸收光谱数据表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_uv_spectra (
    id              INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    experiment_id   INT UNSIGNED NOT NULL,
    sample_no       VARCHAR(64) COMMENT '样品编号（xlsx 列头）',
    peak_index      INT UNSIGNED NOT NULL COMMENT '峰序号',
    lambda_values   JSON NOT NULL COMMENT '最大吸收波长数组',
    INDEX idx_exp_sample_peak (experiment_id, sample_no, peak_index),
    CONSTRAINT fk_raw_uv_exp FOREIGN KEY (experiment_id) REFERENCES raw_experiments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原始紫外吸收光谱数据';

-- -----------------------------------------------------
-- 11. 检测任务表（多药物批量检测）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_tasks (
    id                      INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    task_no                 VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    name                    VARCHAR(128) COMMENT '任务名称',
    category_id             INT UNSIGNED NOT NULL,
    reference_drug_id       INT UNSIGNED,
    reference_retention_time DOUBLE COMMENT '参照保留时间',
    operator_id             INT UNSIGNED,
    status                  TINYINT DEFAULT 0 COMMENT '0-待检测，1-检测中，2-完成，3-失败',
    threshold_rrt           DOUBLE DEFAULT 0.60 COMMENT 'RRT 阈值',
    threshold_peak_area     DOUBLE DEFAULT 0.60 COMMENT '峰面积阈值',
    threshold_uv            DOUBLE DEFAULT 2.00 COMMENT '紫外阈值',
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_status (status),
    CONSTRAINT fk_task_category FOREIGN KEY (category_id) REFERENCES drug_categories(id),
    CONSTRAINT fk_task_ref_drug FOREIGN KEY (reference_drug_id) REFERENCES reference_drugs(id) ON DELETE SET NULL,
    CONSTRAINT fk_task_operator FOREIGN KEY (operator_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测任务表';

-- -----------------------------------------------------
-- 12. 检测结果表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_results (
    id                  INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    task_id             INT UNSIGNED NOT NULL,
    sample_no           VARCHAR(64) NOT NULL COMMENT '样品编号',
    peak_index          INT UNSIGNED NOT NULL COMMENT '峰序号',
    detected_drug_id    INT UNSIGNED COMMENT '检出的药物',
    detection_method    ENUM('rrt','peak_area','uv_spectrum','combined') DEFAULT 'combined' COMMENT '判定依据',
    confidence          DOUBLE COMMENT '确信度/后验概率',
    conclusion          VARCHAR(255) COMMENT '结论文本',
    is_positive         TINYINT DEFAULT 0 COMMENT '是否阳性 0/1',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_sample (task_id, sample_no),
    INDEX idx_detected_drug (detected_drug_id),
    CONSTRAINT fk_result_task FOREIGN KEY (task_id) REFERENCES detection_tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_result_drug FOREIGN KEY (detected_drug_id) REFERENCES reference_drugs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测结果表';

-- -----------------------------------------------------
-- 13. 检测峰值匹配明细表（峰值图对比）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS detection_peak_matches (
    id                  INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    result_id           INT UNSIGNED NOT NULL,
    peak_index          INT UNSIGNED NOT NULL COMMENT '样品峰序号',
    sample_peak_rt      DOUBLE COMMENT '样品峰保留时间',
    ref_drug_id         INT UNSIGNED COMMENT '比对的对照品',
    ref_peak_rt         DOUBLE COMMENT '对照品保留时间',
    similarity_score    DOUBLE COMMENT '相似度得分',
    matched_wavelengths JSON COMMENT '匹配到的波长及面积对比',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_match_result FOREIGN KEY (result_id) REFERENCES detection_results(id) ON DELETE CASCADE,
    CONSTRAINT fk_match_ref_drug FOREIGN KEY (ref_drug_id) REFERENCES reference_drugs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='检测峰值匹配明细';

-- -----------------------------------------------------
-- 14. 系统配置表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS system_configs (
    id          INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    config_key  VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    description VARCHAR(255),
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- -----------------------------------------------------
-- 15. 操作日志表
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS operation_logs (
    id          INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    user_id     INT UNSIGNED,
    action      VARCHAR(100) NOT NULL COMMENT '操作类型',
    target_type VARCHAR(64) COMMENT '操作对象类型',
    target_id   VARCHAR(64) COMMENT '操作对象 id',
    detail      TEXT COMMENT '详情',
    ip_address  VARCHAR(64),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, created_at),
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- drug_categories 的 reference_drug_id 外键（reference_drugs 已创建）
ALTER TABLE drug_categories
    ADD CONSTRAINT fk_cat_ref_drug FOREIGN KEY (reference_drug_id) REFERENCES reference_drugs(id) ON DELETE SET NULL;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------
-- 种子数据
-- -----------------------------------------------------

-- 管理员账号（默认密码 admin123，部署前请务必修改）
INSERT INTO users (id, username, password_hash, real_name, role, status) VALUES
(1, 'admin', '$2b$12$oWzRzs5tZ7.2scxUrOEpUuqutGNJk1AkiOEGZ/m6IZJiHh3tm2jx6', '系统管理员', 'admin', 1)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 药物类别（1-8，与原系统一致）
INSERT INTO drug_categories (id, code, name, wavelengths) VALUES
(1, '1', '安神镇定类', '[245, 250, 255, 260]'),
(2, '2', '减肥类', '[245, 248, 250, 254]'),
(3, '3', '降糖类', '[]'),
(4, '4', '降压类', '[]'),
(5, '5', '降脂类', '[]'),
(6, '6', '抗感冒类', '[]'),
(7, '7', '消肿止痛抗风湿类', '[]'),
(8, '8', '止咳平喘类', '[]')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 安神镇定类 9 种对照品
INSERT INTO reference_drugs (id, category_id, name, is_reference) VALUES
(1, 1, '咪达唑仑', 0),
(2, 1, '苯巴比妥', 0),
(3, 1, '盐酸氯丙嗪', 1),
(4, 1, '艾司唑仑', 0),
(5, 1, '奥沙西泮', 0),
(6, 1, '阿普唑仑', 0),
(7, 1, '三唑仑', 0),
(8, 1, '氯硝西泮', 0),
(9, 1, '地西泮', 0)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 设置安神镇定类默认参照物为盐酸氯丙嗪
UPDATE drug_categories SET reference_drug_id = 3 WHERE code = '1';

-- 相对保留时间初始参数（单样本，方差为 0，需后续导入训练数据后更新）
INSERT INTO rrt_model_params (id, drug_id, sample_count, mean, variance, std_dev) VALUES
(1, 1, 1, 0.4816753926701571, 0.0, 0.0),
(2, 2, 1, 0.8331536803202957, 0.0, 0.0),
(3, 3, 1, 1.0, 0.0, 0.0),
(4, 4, 1, 1.2985063135201724, 0.0, 0.0),
(5, 5, 1, 1.3423159839852172, 0.0, 0.0),
(6, 6, 1, 1.3855097012627042, 0.0, 0.0),
(7, 7, 1, 1.503849707422236, 0.0, 0.0),
(8, 8, 1, 1.548660301817062, 0.0, 0.0),
(9, 9, 1, 1.8580997844163845, 0.0, 0.0)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 峰面积比值初始参数（单样本，协方差矩阵为空，需后续训练拟合）
INSERT INTO peak_area_model_params (id, drug_id, sample_count, wavelengths, mean_vector, covariance_matrix) VALUES
(1, 1, 1, '[245, 250, 255, 260]', '[1.1372998885983274, 0.8114931174008272, 0.5800898198257914]', NULL),
(2, 2, 1, '[245, 250, 255, 260]', '[1.4647763205639937, 0.7415334388381862, 0.6366648675954752]', NULL),
(3, 3, 1, '[245, 250, 255, 260]', '[0.7451227772507883, 1.1696900568282356, 0.9104673783951734]', NULL),
(4, 4, 1, '[245, 250, 255, 260]', '[1.1220843517724284, 0.7486058472120207, 0.5224184698869524]', NULL),
(5, 5, 1, '[245, 250, 255, 260]', '[1.1371148667624853, 0.8480861046405974, 0.634317402102504]', NULL),
(6, 6, 1, '[245, 250, 255, 260]', '[1.1274741523622003, 0.7717890127907021, 0.5712634409631908]', NULL),
(7, 7, 1, '[245, 250, 255, 260]', '[1.2152374534794108, 0.737230800212223, 0.49092049771705415]', NULL),
(8, 8, 1, '[245, 250, 255, 260]', '[1.0223510306530494, 0.9537001395895399, 0.8670035601869135]', NULL),
(9, 9, 1, '[245, 250, 255, 260]', '[1.1547437463578551, 0.8138805084752102, 0.6436417034652647]', NULL)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 紫外吸收光谱初始参数
INSERT INTO uv_spectrum_model_params (id, drug_id, sample_count, peak_count, lambda_max_1, lambda_max_2, absorption_data) VALUES
(1, 1, 1, 1, 227.5, NULL, '{"A245": 1595667.0, "A250": 1403031.0, "R1": 1.1372998885983274, "A255": 1138550.0, "R2": 0.8114931174008272, "A260": 813884.0, "R3": 0.5800898198257914}'),
(2, 2, 1, 1, 222.7, NULL, '{"A245": 1441107.0, "A250": 983841.0, "R1": 1.4647763205639937, "A255": 729551.0, "R2": 0.7415334388381862, "A260": 626377.0, "R3": 0.6366648675954752}'),
(3, 3, 1, 2, 255.8, 308.1, '{"A245": 3010872.0, "A250": 4040773.0, "R1": 0.7451227772507883, "A255": 4726452.0, "R2": 1.1696900568282356, "A260": 3678992.0, "R3": 0.9104673783951734}'),
(4, 4, 1, 1, 225.1, NULL, '{"A245": 1547526.0, "A250": 1379153.0, "R1": 1.1220843517724284, "A255": 1032442.0, "R2": 0.7486058472120207, "A260": 720495.0, "R3": 0.5224184698869524}'),
(5, 5, 1, 2, 228.6, 312.9, '{"A245": 2064921.0, "A250": 1815930.0, "R1": 1.1371148667624853, "A255": 1540065.0, "R2": 0.8480861046405974, "A260": 1151876.0, "R3": 0.634317402102504}'),
(6, 6, 1, 1, 223.9, NULL, '{"A245": 1177304.0, "A250": 1044196.0, "R1": 1.1274741523622003, "A255": 805899.0, "R2": 0.7717890127907021, "A260": 596511.0, "R3": 0.5712634409631908}'),
(7, 7, 1, 1, 225.1, NULL, '{"A245": 1568987.0, "A250": 1291095.0, "R1": 1.2152374534794108, "A255": 951835.0, "R2": 0.737230800212223, "A260": 633825.0, "R3": 0.49092049771705415}'),
(8, 8, 1, 2, 220.4, 310.5, '{"A245": 1407669.0, "A250": 1376894.0, "R1": 1.0223510306530494, "A255": 1313144.0, "R2": 0.9537001395895399, "A260": 1193772.0, "R3": 0.8670035601869135}'),
(9, 9, 1, 2, 231.0, 360.1, '{"A245": 3087279.0, "A250": 2673562.0, "R1": 1.1547437463578551, "A255": 2175960.0, "R2": 0.8138805084752102, "A260": 1720816.0, "R3": 0.6436417034652647}')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 默认系统配置（阈值、权重）
INSERT INTO system_configs (config_key, config_value, description) VALUES
('threshold_rrt', '0.60', '相对保留时间后验概率阈值'),
('threshold_peak_area', '0.60', '峰面积比值后验概率阈值'),
('threshold_uv', '2.0', '紫外吸收光谱欧氏距离阈值（nm）'),
('weight_rrt', '0.25', '加权组合时 RRT 权重'),
('weight_peak_area', '0.35', '加权组合时峰面积权重'),
('weight_uv', '0.40', '加权组合时紫外光谱权重'),
('detection_mode', 'weighted', '检测组合模式：weighted / strict')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Schema generation complete.
