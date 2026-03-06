-- Assumptions made regarding present data and future data:
-- - Subject numbers are unique across projects, i.e., new projects use new subject numbers and the same patient will not have the same subject number across projects.
-- - Sample numbers are unique across projects and subjects, i.e., the same sample number will not be used in different projects or subjects.
-- - Each subject can have multiple conditions and treatments. This allows analysis of potential relationships between other conditions and treatments and the responses and samples of the treatment of interest.
-- For ease of use, attributes have the same name as in the CSV file.
-- Subject and sample attributes are defined as VARCHAR(255) to account for larger numbers in future data, while other attributes are defined with appropriate data types based on their expected values.
-- Performance indexes for common analytical queries are created to optimize query performance for analyses that filter by these attributes.
-- The schema is designed to be flexible and scalable to accommodate future data additions and changes while maintaining data integrity through the use of foreign keys and unique constraints, as well as properly balancing normalization to avoid data inconsistencies and redundancy for performance of specific queries. 

DROP TABLE IF EXISTS subjects;

CREATE TABLE subjects (
    subject VARCHAR(255) PRIMARY KEY,
    project VARCHAR(50) NOT NULL,
    age INT NOT NULL,
    sex VARCHAR(10) NOT NULL
);

DROP TABLE IF EXISTS conditions;

CREATE TABLE conditions (
    condition_id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL,
    FOREIGN KEY (subject) REFERENCES subjects(subject),
    UNIQUE(subject, condition)
);

DROP TABLE IF EXISTS treatments;

CREATE TABLE treatments (
    treatment_id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    treatment VARCHAR(50) NOT NULL,
    response VARCHAR(10),
    FOREIGN KEY (subject) REFERENCES subjects(subject),
    UNIQUE(subject, treatment)
);

DROP TABLE IF EXISTS samples;

CREATE TABLE samples (
    sample VARCHAR(255) PRIMARY KEY,
    subject VARCHAR(255) NOT NULL,
    sample_type VARCHAR(50) NOT NULL,
    time_from_treatment_start INT NOT NULL,
    b_cell INT NOT NULL,
    cd8_t_cell INT NOT NULL,
    cd4_t_cell INT NOT NULL,
    nk_cell INT NOT NULL,
    monocyte INT NOT NULL,
    FOREIGN KEY (subject) REFERENCES subjects(subject)
);

CREATE INDEX idx_subjects_project ON subjects(project);
CREATE INDEX idx_conditions_subject ON conditions(subject);
CREATE INDEX idx_treatments_subject ON treatments(subject);
CREATE INDEX idx_samples_subject ON samples(subject);
CREATE INDEX idx_samples_time ON samples(time_from_treatment_start);
