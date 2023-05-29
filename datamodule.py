from collections import defaultdict
import os
import defusedxml.ElementTree as ET


class HealthDataProcessor:
    def __init__(self, input_dir):
        self.input_dir = input_dir
        if not os.path.isdir(self.input_dir):
            raise OSError("`input_dir` must be a valid directory")

    def _get_smoking_status(self, root):
        smoker_tag = root[1].find('SMOKER')
        if smoker_tag is not None:
            if smoker_tag.get('status') == 'ever':
                return ['past']
            return [smoker_tag.get('status', 'unknown')]
        return ['unknown']

    def _get_diabetes_status(self, root):
        db_tags = root[1].findall('DIABETES')
        if any(tag.get('indicator') in ('A1C', 'glucose') for tag in db_tags):
            return ["test"]
        if any(tag.get('indicator') == 'mention' for tag in db_tags):
            return ["mention"]
        return ["unknown"]

    def _get_hypertension_status(self, root):
        db_tags = root[1].findall('HYPERTENSION')
        if not db_tags:
            return ["unknown"]
        indicators = []
        for tag in db_tags:
            indicator = tag.get('indicator')
            if indicator not in indicators:
                indicators.append(indicator)
        return indicators

    def read_i2b2_xml_file(self, fpath):
        tree = ET.parse(fpath)
        root = tree.getroot()
        data = {
            'text': root[0].text,
            'labels': {
                'smoking': self._get_smoking_status(root),
                'diabetes': self._get_diabetes_status(root),
                'hypertension': self._get_hypertension_status(root)
            }
        }
        return data

    def read_and_transform_data(self):
        docs, labels = [], defaultdict(list)
        for filename in os.listdir(self.input_dir):
            if not filename.endswith('.xml'):
                continue
            data = self.read_i2b2_xml_file(
                os.path.join(self.input_dir, filename))
            docs.append(data['text'])
            for label in data['labels']:
                labels[label].append(data['labels'][label])
        return (docs, labels)

if __name__=="__main__":
    datadirs = [
        'data/I2B2/2014 De-identification and Heart Disease Risk Factors Challenge/training-PHI-Gold-Set1/', 
        'data/I2B2/2014 De-identification and Heart Disease Risk Factors Challenge/training-PHI-Gold-Set2/', 
    ]
    for datadir in datadirs:
        processor = HealthDataProcessor(
            input_dir=datadir)
        docs, labels = processor.read_and_transform_data()
        print(len(docs), len(labels))
