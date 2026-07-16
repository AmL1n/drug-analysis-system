-- 增量高斯 RRT 学习模型字段迁移
-- 为 drugs 表添加 RRT 训练计数、均值、标准差三列
-- 兼容 SQLite / MySQL

ALTER TABLE drugs ADD COLUMN rrt_training_count INTEGER DEFAULT 0 COMMENT 'RRT 训练样本数 N';
ALTER TABLE drugs ADD COLUMN rrt_mean NUMERIC(12, 6) COMMENT 'RRT 均值 μ';
ALTER TABLE drugs ADD COLUMN rrt_std NUMERIC(12, 6) COMMENT 'RRT 标准差 σ';

-- 可选：基于现有参考峰为所有药物初始化 RRT 统计量（N=1，μ=参考峰 RRT，σ=1.0）
-- UPDATE drugs
-- SET
--     rrt_training_count = 1,
--     rrt_mean = (SELECT relative_retention_time FROM reference_peaks WHERE reference_peaks.drug_id = drugs.id ORDER BY peak_index LIMIT 1),
--     rrt_std = 1.0
-- WHERE EXISTS (SELECT 1 FROM reference_peaks WHERE reference_peaks.drug_id = drugs.id);
