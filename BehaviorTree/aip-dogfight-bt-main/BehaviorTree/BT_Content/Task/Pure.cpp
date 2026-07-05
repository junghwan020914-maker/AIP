#include "Pure.h"

namespace Action
{
	PortsList Pure::providedPorts()
	{
		return {
			InputPort<CPPBlackBoard*>("BB")
		};
	}

	NodeStatus Pure::tick()
	{
		Optional<CPPBlackBoard*> BB = getInput<CPPBlackBoard*>("BB");

		// 추적점(VP) = 적기의 현재 위치. 내 기수를 적기에 그대로 조준한다.
		(*BB)->VP_Cartesian = (*BB)->TargetLocaion_Cartesian;

		return NodeStatus::SUCCESS;
	}
}
