import argparse
from pathlib import Path

import torch
from tqdm import tqdm

from transformers import BartForConditionalGeneration, BartTokenizer


DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def generate_summaries(lns, out_file, batch_size=8, device=DEFAULT_DEVICE):
    fout = Path(out_file).open("w")
    model = BartForConditionalGeneration.from_pretrained("bart-large-cnn", output_past=True,).to(device)
    tokenizer = BartTokenizer.from_pretrained("bart-large")
    for batch in tqdm(list(chunks(lns, batch_size))):
        dct = tokenizer.batch_encode_plus(batch, max_length=1024, return_tensors="pt", pad_to_max_length=True)
        summaries = model.generate(
            input_ids=dct["input_ids"].to(device),
            attention_mask=dct["attention_mask"].to(device),
            num_beams=4,
            length_penalty=2.0,
            max_length=140,
            min_len=55,
            no_repeat_ngram_size=3,
        )
        dec = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in summaries]
        for hypothesis in dec:
            fout.write(hypothesis + "\n")
            fout.flush()


def _run_generate():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source_path", type=str, help="like cnn_dm/test.source",
    )
    parser.add_argument(
        "output_path", type=str, help="where to save summaries",
    )
    parser.add_argument(
        "--device", type=str, required=False, default=DEFAULT_DEVICE, help="cuda, cuda:1, cpu etc.",
    )
    parser.add_argument(
        "--bs", type=int, default=8, required=False, help="batch size: how many to summarize at a time",
    )
    args = parser.parse_args()
    lns = [" " + x.rstrip() for x in open(args.source_path).readlines()]
    generate_summaries(lns, args.output_path, batch_size=args.bs, device=args.device)


if __name__ == "__main__":
    _run_generate()
