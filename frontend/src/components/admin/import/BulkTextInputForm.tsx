import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type Props = {
  placeholder: string;
  onSubmit: (lines: string[]) => Promise<void>;
  loading?: boolean;
  title?: string;
};

export const BulkTextInputForm = ({
  placeholder,
  onSubmit,
  loading = false,
  title = "一括登録フォーム",
}: Props) => {
  const [input, setInput] = useState("");

  const handleSubmit = async () => {
    const lines = input
      .trim()
      .replace(/\t/g, ",")
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line !== "");

    await onSubmit(lines);
    setInput("");
  };

  return (
    <div className=" p-6">
      <h2 className="text-lg font-bold">{title}</h2>
      <Textarea
        placeholder={placeholder}
        className="min-h-[200px] font-mono"
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <Button onClick={handleSubmit} disabled={loading}>
        {loading ? "登録中..." : "登録する"}
      </Button>
    </div>
  );
};


