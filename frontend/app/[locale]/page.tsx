import { unstable_setRequestLocale } from "next-intl/server";
import KBSearch from "@/components/KBSearch";

export default function HomePage({
  params,
}: {
  params: { locale: string };
}) {
  unstable_setRequestLocale(params.locale);
  return <KBSearch />;
}
