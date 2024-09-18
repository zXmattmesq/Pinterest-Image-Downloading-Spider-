with open('formatted_keywords.txt', 'r') as input_file:
    with open('keyword.txt', 'w') as output_file:
        for line in input_file:
            line = line.strip('\n')
            line_with_comma = line + ',' + '\n'
            output_file.write(line_with_comma)

print('Comma added to the end of each line in the output file.')